"""Audit helper. Every memory write/recall, isolation block, maintenance run,
and HITL decision lands here — this is the compliance/inspector surface."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AuditLog


async def record(db: AsyncSession, member_id, event_type: str, detail: dict) -> None:
    db.add(AuditLog(member_id=member_id, event_type=event_type, detail=detail))
    # caller owns the commit boundary; flush so it's visible within the txn
    await db.flush()
