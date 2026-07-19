"""In-memory tap of the prompts sent to the model provider (Qwen Cloud / Ollama).

Captured in the chat router at the exact point the `messages` array is assembled —
that array IS the literal payload handed to `client.stream()` and put on the wire to
DashScope. A bounded, per-principal ring buffer; it holds nothing durable and resets
on restart.

Isolation: entries are tagged with the principal and read back ONLY through the
auth-scoped `/api/inspector/prompts` endpoint, so a principal sees only their own
prompts — same boundary as every other inspector view. This is not a god-view.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any

_MAX = 50
_buffer: "deque[dict[str, Any]]" = deque(maxlen=_MAX)


def record(member_id: str, *, kind: str, model: str, base_url: str,
           provider: str, messages: list[dict]) -> None:
    """Append one captured prompt. `messages` is copied shallowly (role + content)."""
    _buffer.append({
        "member_id": str(member_id),
        "kind": kind,
        "model": model,
        "base_url": base_url,
        "provider": provider,
        "messages": [{"role": m.get("role"), "content": m.get("content")} for m in messages],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def recent(member_id: str, limit: int = 20) -> list[dict]:
    """Most-recent-first prompts for one principal. Never returns another's."""
    out = [p for p in reversed(_buffer) if p["member_id"] == str(member_id)]
    return out[:limit]
