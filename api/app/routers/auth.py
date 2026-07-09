from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth
from app.db import Member, get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    mode: str = "principal"          # "principal" | "supervisor" | "demo"
    member_id: str | None = None     # required when mode == "principal"


@router.post("/login")
async def login(body: LoginIn, db: AsyncSession = Depends(get_session)):
    """Dummy login — no password. Establishes a signed, server-verifiable identity.
    A principal login is bound to one member; the wall is then enforced server-side."""
    if body.mode == "principal":
        if not body.member_id:
            raise HTTPException(400, "member_id required for a principal login")
        member = await db.get(Member, body.member_id)
        if not member:
            raise HTTPException(404, "principal not found")
        return {
            "token": auth.make_token("principal", str(member.id)),
            "role": "principal",
            "member_id": str(member.id),
            "name": member.name,
        }
    if body.mode in ("supervisor", "demo"):
        return {"token": auth.make_token(body.mode), "role": body.mode, "member_id": None, "name": None}
    raise HTTPException(400, "unknown login mode")


@router.get("/me")
async def me(ident: dict = Depends(auth.require_identity)):
    return ident
