"""The memory engine — where the judging points are won.

Write path:  extract -> embed -> dedup/supersede -> persist (PG + Qdrant) -> audit
Read path:   embed query -> namespace-filtered candidates -> rerank -> bounded top-k
Forgetting:  supersession (write-time) + expiry + salience decay/prune (maintenance)
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record
from app.config import get_settings
from app.db import Memory
from app.llm import client, prompts
from app.memory import embeddings
from app.memory import qdrant_client as vec

_s = get_settings()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── WRITE PATH ───────────────────────────────────────────────────────────────
async def write_memories(db: AsyncSession, member, source_message_id, user_text: str,
                         recent_context: str) -> list[Memory]:
    """Extract durable memories from a turn and persist them. Non-blocking to the
    user's response (call this after streaming the reply)."""
    candidates = await client.complete_json(prompts.extraction_messages(user_text, recent_context))
    if not isinstance(candidates, list) or not candidates:
        return []

    written: list[Memory] = []
    for c in candidates[:4]:
        content = (c.get("content") or "").strip()
        if not content:
            continue
        kind = c.get("kind", "fact")
        salience = float(c.get("salience", 0.5))
        vector = await embeddings.embed(content)

        # dedup / supersession check against this member's existing memories.
        # Scan the nearest neighbors above a lower floor and let the LLM classify the
        # relationship three ways. This catches updates that reword a fact
        # (e.g. "$4.2M ceiling" -> "raised to $5.0M"), which a high cosine cutoff misses,
        # without wrongly merging merely-similar-but-distinct memories.
        near = await vec.search(member.memory_namespace, vector, limit=12, active_only=True)
        superseded_old = None
        skip = False
        for cand in near:
            if cand["score"] < _s.supersede_scan_floor:
                break  # neighbors are score-sorted; nothing else is close enough
            old = await db.get(Memory, cand["memory_id"])
            if not old:
                continue
            verdict = await client.complete_json(prompts.supersede_messages(old.content, content))
            relation = verdict.get("relation") if isinstance(verdict, dict) else None
            if relation == "supersedes":
                superseded_old = old
                break
            if relation == "duplicate":
                skip = True  # nothing new to store
                break
            # "distinct" -> keep scanning remaining neighbors, then store as new
        if skip:
            continue

        point_id = vec.new_point_id()
        mem = Memory(
            member_id=member.id,
            namespace=member.memory_namespace,
            kind=kind,
            content=content,
            salience=salience,
            status="active",
            source_message_id=source_message_id,
            qdrant_point_id=point_id,
        )
        db.add(mem)
        await db.flush()  # get mem.id

        if superseded_old is not None:
            superseded_old.status = "superseded"
            superseded_old.superseded_by = mem.id
            await vec.set_status(member.memory_namespace, str(superseded_old.qdrant_point_id), "superseded")

        await vec.upsert(
            member.memory_namespace, str(member.id), str(mem.id), point_id, vector,
            payload_extra={"kind": kind, "salience": salience},
        )
        await record(db, member.id, "memory_write",
                     {"memory_id": str(mem.id), "kind": kind,
                      "superseded": str(superseded_old.id) if superseded_old else None})
        written.append(mem)

    await db.commit()
    return written


# ── READ PATH (bounded recall) ───────────────────────────────────────────────
def _recency_score(last_used: datetime | None) -> float:
    if last_used is None:
        return 0.3
    age_days = (_now() - last_used).total_seconds() / 86400.0
    return math.exp(-age_days / 30.0)  # ~half-life of a few weeks


async def recall(db: AsyncSession, member, query: str) -> dict:
    """Return bounded top-k memories for THIS member plus a trace for the inspector."""
    qvec = await embeddings.embed(query)
    candidates = await vec.search(member.memory_namespace, qvec, limit=_s.k_candidates, active_only=True)

    scored = []
    for c in candidates:
        mem = await db.get(Memory, c["memory_id"])
        if not mem or mem.status != "active":
            continue
        blended = (
            _s.w_sim * c["score"]
            + _s.w_sal * float(mem.salience)
            + _s.w_rec * _recency_score(mem.last_used_at)
        )
        scored.append((blended, c["score"], mem))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[: _s.k_context]

    selected = [{
        "id": str(m.id), "kind": m.kind, "content": m.content,
        "salience": round(float(m.salience), 2),
        "similarity": round(sim, 3), "blended": round(b, 3),
    } for (b, sim, m) in top]

    # bump recency for what we actually used
    now = _now()
    if top:
        ids = [m.id for (_, _, m) in top]
        await db.execute(update(Memory).where(Memory.id.in_(ids)).values(last_used_at=now))
        await db.commit()

    approx_tokens = sum(len(m["content"]) for m in selected) // 4
    trace = {
        "query": query,
        "candidates_considered": len(candidates),
        "selected_count": len(selected),
        "approx_tokens": approx_tokens,
        "token_budget": _s.k_context,  # informational
        "selected": selected,
    }
    await record(db, member.id, "memory_recall",
                 {"candidates": len(candidates), "selected": [m["id"] for m in selected]})
    return {"memories": selected, "trace": trace}


# ── FORGETTING ───────────────────────────────────────────────────────────────
async def run_maintenance(db: AsyncSession, member) -> dict:
    """Expiry sweep + salience-decay prune. Exposed as a button in the inspector
    so judges can watch forgetting happen live."""
    now = _now()
    expired = 0
    pruned = 0

    # expiry: anything past expires_at -> expired
    rows = (await db.execute(
        select(Memory).where(Memory.member_id == member.id, Memory.status == "active")
    )).scalars().all()

    for m in rows:
        if m.expires_at is not None and m.expires_at < now:
            m.status = "expired"
            await vec.set_status(member.memory_namespace, str(m.qdrant_point_id), "expired")
            expired += 1
            continue
        # salience decay + prune: low salience and unused for > 30 days
        unused_days = (now - (m.last_used_at or m.created_at)).total_seconds() / 86400.0
        if float(m.salience) < _s.salience_prune_floor and unused_days > 30:
            m.status = "expired"
            await vec.set_status(member.memory_namespace, str(m.qdrant_point_id), "expired")
            pruned += 1

    await db.commit()
    summary = {"expired": expired, "pruned": pruned}
    await record(db, member.id, "memory_maintenance", summary)
    return summary
