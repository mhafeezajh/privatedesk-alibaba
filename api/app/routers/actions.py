from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record
from app.db import ProposedAction, get_session

router = APIRouter(prefix="/api/actions", tags=["actions"])


@router.get("/pending")
async def pending(member_id: str, db: AsyncSession = Depends(get_session)):
    rows = (await db.execute(
        select(ProposedAction).where(
            ProposedAction.member_id == member_id, ProposedAction.status == "pending"
        )
    )).scalars().all()
    return [{"id": str(a.id), "action_type": a.action_type, "payload": a.payload} for a in rows]


async def _resolve(action_id: str, status: str, db: AsyncSession):
    a = await db.get(ProposedAction, action_id)
    if not a:
        raise HTTPException(404, "action not found")
    a.status = status
    a.resolved_at = datetime.now(timezone.utc)
    await record(db, a.member_id, f"hitl_{status}", {"action_id": action_id, "action_type": a.action_type})
    await db.commit()
    return {"id": action_id, "status": status}


@router.post("/{action_id}/approve")
async def approve(action_id: str, db: AsyncSession = Depends(get_session)):
    return await _resolve(action_id, "approved", db)


@router.post("/{action_id}/reject")
async def reject(action_id: str, db: AsyncSession = Depends(get_session)):
    return await _resolve(action_id, "rejected", db)
