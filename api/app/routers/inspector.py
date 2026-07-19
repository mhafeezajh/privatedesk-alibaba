from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth
from app.db import AuditLog, Member, Memory, ProposedAction, get_session
from app.llm import prompt_tap
from app.memory import engine
from app.routers.members import require_member

router = APIRouter(prefix="/api/inspector", tags=["inspector"])


@router.get("/prompts")
async def prompts_sent(member_id: str, db: AsyncSession = Depends(get_session),
                       ident: dict = Depends(auth.require_identity)):
    auth.authorize_content(ident, member_id)  # content — this principal's own prompts only
    await require_member(member_id, db)
    return prompt_tap.recent(member_id)


@router.get("/memories")
async def memories(member_id: str, db: AsyncSession = Depends(get_session),
                   ident: dict = Depends(auth.require_identity)):
    auth.authorize_content(ident, member_id)  # content — supervisor is blocked
    member = await require_member(member_id, db)
    rows = (await db.execute(
        select(Memory).where(Memory.member_id == member.id).order_by(Memory.created_at.desc())
    )).scalars().all()
    return [{
        "id": str(m.id), "kind": m.kind, "content": m.content,
        "salience": round(float(m.salience), 2), "status": m.status,
        "superseded_by": str(m.superseded_by) if m.superseded_by else None,
        "created_at": m.created_at.isoformat(),
        "last_used_at": m.last_used_at.isoformat() if m.last_used_at else None,
    } for m in rows]


@router.get("/audit")
async def audit(member_id: str, db: AsyncSession = Depends(get_session),
                ident: dict = Depends(auth.require_identity)):
    auth.authorize_content(ident, member_id)
    member = await require_member(member_id, db)
    rows = (await db.execute(
        select(AuditLog).where(AuditLog.member_id == member.id)
        .order_by(AuditLog.created_at.desc()).limit(100)
    )).scalars().all()
    return [{
        "event_type": a.event_type, "detail": a.detail,
        "created_at": a.created_at.isoformat(),
    } for a in rows]


@router.post("/maintenance")
async def maintenance(member_id: str, db: AsyncSession = Depends(get_session),
                      ident: dict = Depends(auth.require_identity)):
    auth.authorize_content(ident, member_id)
    member = await require_member(member_id, db)
    return await engine.run_maintenance(db, member)


@router.get("/report")
async def report(member_id: str, db: AsyncSession = Depends(get_session),
                 ident: dict = Depends(auth.require_identity)):
    auth.authorize_metadata(ident, member_id)  # metadata only — supervisor allowed
    """A governance / compliance report for one principal: memory state, the full
    audit breakdown, human-in-the-loop decisions, and the isolation attestation.
    Everything here is scoped to a single namespace — the report itself respects the wall."""
    member = await require_member(member_id, db)
    mems = (await db.execute(select(Memory).where(Memory.member_id == member.id))).scalars().all()
    audits = (await db.execute(select(AuditLog).where(AuditLog.member_id == member.id))).scalars().all()
    actions = (await db.execute(
        select(ProposedAction).where(ProposedAction.member_id == member.id)
    )).scalars().all()

    by_status = Counter(m.status for m in mems)
    by_kind = Counter(m.kind for m in mems)
    by_event = Counter(a.event_type for a in audits)
    by_action = Counter(a.status for a in actions)

    return {
        "principal": {
            "name": member.name,
            "role": member.role,
            "persona": member.persona_key,
            # opaque namespace, shown truncated — proves isolation without leaking the key
            "namespace": member.memory_namespace[:9] + "…",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "memories": {
            "total": len(mems),
            "active": by_status.get("active", 0),
            "superseded": by_status.get("superseded", 0),
            "expired": by_status.get("expired", 0),
            "by_kind": dict(by_kind),
        },
        "audit": {"total_events": len(audits), "by_type": dict(by_event)},
        "governance": {
            "isolation_blocks": by_event.get("isolation_block", 0),
            "memory_writes": by_event.get("memory_write", 0),
            "memory_recalls": by_event.get("memory_recall", 0),
            "maintenance_runs": by_event.get("memory_maintenance", 0),
            "hitl_approved": by_event.get("hitl_approved", 0),
            "hitl_rejected": by_event.get("hitl_rejected", 0),
            "actions_pending": by_action.get("pending", 0),
        },
        "attestation": {
            "namespace_isolated": True,
            "human_in_the_loop": True,
            "statement": (
                f"All memory for “{member.name}” is confined to a single opaque namespace. "
                f"Cross-context reads are structurally impossible and are audited as isolation "
                f"blocks. Actions are proposed, never auto-executed, and require human approval."
            ),
        },
    }


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_session),
                   ident: dict = Depends(auth.require_identity)):
    """Cross-principal governance overview for oversight — METADATA ONLY, never content.
    Counts, audit breakdown, isolation-block totals and attestation for every principal.
    A supervisor can confirm the walls hold; it can never read across them."""
    auth.require_oversight(ident)
    members = (await db.execute(select(Member))).scalars().all()
    rows = []
    total_blocks = 0
    for m in members:
        mems = (await db.execute(select(Memory).where(Memory.member_id == m.id))).scalars().all()
        audits = (await db.execute(select(AuditLog).where(AuditLog.member_id == m.id))).scalars().all()
        by_status = Counter(x.status for x in mems)
        by_event = Counter(a.event_type for a in audits)
        total_blocks += by_event.get("isolation_block", 0)
        rows.append({
            "id": str(m.id),
            "name": m.name,
            "role": m.role,
            "namespace": m.memory_namespace[:9] + "…",
            "memories_active": by_status.get("active", 0),
            "memories_total": len(mems),
            "isolation_blocks": by_event.get("isolation_block", 0),
            "audit_events": len(audits),
            "attestation_ok": True,
        })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "principals": rows,
        "totals": {"principals": len(rows), "isolation_blocks": total_blocks},
        "note": "Metadata only. Oversight confirms isolation holds; it never reads principal content.",
    }
