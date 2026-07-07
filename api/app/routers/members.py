from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Member, get_session

router = APIRouter(prefix="/api", tags=["members"])


@router.get("/members")
async def list_members(db: AsyncSession = Depends(get_session)):
    rows = (await db.execute(select(Member))).scalars().all()
    return [
        {"id": str(m.id), "name": m.name, "role": m.role, "persona_key": m.persona_key}
        for m in rows
    ]


async def require_member(member_id: str, db: AsyncSession) -> Member:
    m = await db.get(Member, member_id)
    if not m:
        raise HTTPException(404, "member not found")
    return m
