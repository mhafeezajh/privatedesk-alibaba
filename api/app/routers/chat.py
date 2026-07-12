from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth
from app.audit import record
from app.db import Memory, Message, ProposedAction, Session, SessionLocal, get_session
from app.llm import cache_isolation, client, prompts
from app.memory import engine
from app.personas import get_persona
from app.routers.members import require_member

router = APIRouter(prefix="/api", tags=["chat"])


class ChatIn(BaseModel):
    session_id: str
    message: str


class StartIn(BaseModel):
    member_id: str


@router.post("/session/start")
async def start_session(body: StartIn, db: AsyncSession = Depends(get_session),
                        ident: dict = Depends(auth.require_identity)):
    auth.authorize_content(ident, body.member_id)
    member = await require_member(body.member_id, db)
    s = Session(member_id=member.id)
    db.add(s)
    await db.commit()
    return {"session_id": str(s.id)}


async def _recent_context(db: AsyncSession, session_id: str, limit: int = 6) -> str:
    rows = (await db.execute(
        select(Message).where(Message.session_id == session_id)
        .order_by(Message.created_at.desc()).limit(limit)
    )).scalars().all()
    rows.reverse()
    return "\n".join(f"{m.role}: {m.content}" for m in rows)


@router.post("/chat")
async def chat(body: ChatIn, db: AsyncSession = Depends(get_session),
               ident: dict = Depends(auth.require_identity)):
    sess = await db.get(Session, body.session_id)
    auth.authorize_content(ident, str(sess.member_id))
    member = await require_member(str(sess.member_id), db)
    persona = get_persona(member.persona_key)

    # persist the user's message
    db.add(Message(session_id=sess.id, member_id=member.id, role="user", content=body.message))
    await db.commit()

    # RECALL (bounded, namespace-scoped) before generating
    recalled = await engine.recall(db, member, body.message)
    system_prompt = prompts.compose_system_prompt(
        persona["system_prompt"], member.name, member.role, recalled["memories"]
    )
    # Partition the LLM prompt-cache by principal so a shared provider cache can't become a
    # cross-principal timing side-channel (see llm/cache_isolation.py).
    system_prompt = cache_isolation.with_boundary(system_prompt, member.memory_namespace)
    history = await _recent_context(db, str(sess.id))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": body.message if not history else f"{history}\nuser: {body.message}"},
    ]

    async def gen():
        # surface the recall trace first so the inspector can show bounded recall
        yield f"event: trace\ndata: {json.dumps(recalled['trace'])}\n\n"

        collected: list[str] = []
        async for tok in client.stream(messages):
            collected.append(tok)
            yield f"data: {json.dumps({'token': tok})}\n\n"
        full = "".join(collected)

        # persist assistant message + run write path + HITL detection in a fresh session
        async with SessionLocal() as bg:
            m2 = await bg.get(type(member), member.id)
            bg.add(Message(session_id=sess.id, member_id=member.id, role="assistant", content=full))
            await bg.commit()

            last_msg = (await bg.execute(
                select(Message).where(Message.session_id == sess.id, Message.role == "user")
                .order_by(Message.created_at.desc()).limit(1)
            )).scalars().first()
            await engine.write_memories(bg, m2, last_msg.id if last_msg else None,
                                        body.message, history)

            # governance: if the user asked for another context's data and the assistant
            # declined, record it as an isolation_block — the ethical wall, audited.
            guard = await client.complete_json(prompts.isolation_guard_messages(body.message, full))
            if isinstance(guard, dict) and guard.get("cross_context_denied"):
                await record(bg, member.id, "isolation_block",
                             {"query": body.message[:200], "context": member.name})
                await bg.commit()

            # human-in-the-loop: did the assistant propose an action?
            verdict = await client.complete_json(prompts.hitl_extract_messages(full))
            if isinstance(verdict, dict) and verdict.get("action_type"):
                pa = ProposedAction(member_id=member.id, action_type=verdict["action_type"],
                                    payload=verdict.get("payload", {}))
                bg.add(pa)
                await bg.commit()
                yield f"event: proposed_action\ndata: {json.dumps({'id': str(pa.id), 'action_type': pa.action_type, 'payload': pa.payload})}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
