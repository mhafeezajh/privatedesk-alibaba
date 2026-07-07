from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AuditLog, Memory, get_session
from app.memory import engine
from app.routers.members import require_member

router = APIRouter(prefix="/api/inspector", tags=["inspector"])


@router.get("/memories")
async def memories(member_id: str, db: AsyncSession = Depends(get_session)):
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
async def audit(member_id: str, db: AsyncSession = Depends(get_session)):
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
async def maintenance(member_id: str, db: AsyncSession = Depends(get_session)):
    member = await require_member(member_id, db)
    return await engine.run_maintenance(db, member)
