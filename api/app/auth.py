"""Lightweight, stateless auth for the demo.

A *dummy* login — no passwords — that nevertheless establishes a real, server-side
verifiable identity and enforces the wall at the API. Three roles:

  - "principal"  bound to one member_id; may read/write ONLY that principal's data.
  - "supervisor" compliance/oversight; may read cross-principal METADATA only
                 (governance overview + reports) — never memory content, never chat.
  - "demo"       the demonstration god-view; may read across principals so the
                 side-by-side isolation proof works. The UI labels it as a demo.

Tokens are HMAC-signed with SESSION_SECRET (stateless — survive restarts, no store).
The principal binding is resolved server-side from the token, so a client can never
widen its own access by passing someone else's member_id: the check is here.
"""
from __future__ import annotations

import base64
import hmac
import json
from hashlib import sha256

from fastapi import Header, HTTPException

from app.config import get_settings

ROLES = ("principal", "supervisor", "demo")


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _ub64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _secret() -> bytes:
    return get_settings().session_secret.encode()


def make_token(role: str, member_id: str | None = None) -> str:
    payload = json.dumps({"role": role, "member_id": member_id}, separators=(",", ":")).encode()
    sig = hmac.new(_secret(), payload, sha256).digest()
    return f"{_b64(payload)}.{_b64(sig)}"


def verify_token(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        p_b64, s_b64 = token.split(".", 1)
        payload = _ub64(p_b64)
        if not hmac.compare_digest(_ub64(s_b64), hmac.new(_secret(), payload, sha256).digest()):
            return None
        data = json.loads(payload)
        return data if data.get("role") in ROLES else None
    except Exception:  # noqa: BLE001 — any malformed token is simply unauthenticated
        return None


async def require_identity(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: extract + verify the bearer token, or 401."""
    token = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else None
    ident = verify_token(token)
    if not ident:
        raise HTTPException(status_code=401, detail="not authenticated")
    return ident


# ── authorization helpers (the enforced wall) ────────────────────────────────
def authorize_content(ident: dict, member_id: str) -> None:
    """Read/write a principal's CONTENT (memories, chat, actions, maintenance)."""
    if ident["role"] == "demo":
        return
    if ident["role"] == "principal" and ident.get("member_id") == member_id:
        return
    if ident["role"] == "supervisor":
        raise HTTPException(status_code=403, detail="oversight is metadata-only; it cannot read principal content")
    raise HTTPException(status_code=403, detail="isolation: you may only access your own principal")


def authorize_metadata(ident: dict, member_id: str) -> None:
    """Read a principal's METADATA (governance report) — supervisor/demo any, principal self."""
    if ident["role"] in ("supervisor", "demo"):
        return
    if ident["role"] == "principal" and ident.get("member_id") == member_id:
        return
    raise HTTPException(status_code=403, detail="isolation: you may only access your own principal")


def require_oversight(ident: dict) -> None:
    """Cross-principal metadata (governance overview) — supervisor/demo only."""
    if ident["role"] not in ("supervisor", "demo"):
        raise HTTPException(status_code=403, detail="cross-principal overview is for oversight only")
