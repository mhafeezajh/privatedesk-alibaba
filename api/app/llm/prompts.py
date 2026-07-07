"""Prompt builders for the memory engine and chat.

Kept as plain functions returning message lists so they're trivial to unit-test
and to read in the inspector.
"""
from __future__ import annotations

import json

EXTRACTION_SYSTEM = """You extract durable, reusable memories from a chat turn.
Return ONLY a JSON array (no prose, no code fences). Each item:
{
  "kind": one of ["fact","preference","event","task","relationship"],
  "content": a single self-contained sentence stating the memory in third person,
  "salience": float 0..1 (how important/long-lived this is),
  "expires_at": optional ISO8601 if the memory is inherently time-bounded, else omit,
  "supersedes_hint": optional short text of an older belief this likely replaces, else omit
}
Rules:
- Extract only things worth remembering across sessions. Skip pleasantries and
  one-off chit-chat. If nothing is worth storing, return [].
- Prefer few high-quality memories over many trivial ones (max 4 per turn).
- Never invent facts not present in the user's words."""


def extraction_messages(user_text: str, recent_context: str) -> list[dict]:
    return [
        {"role": "system", "content": EXTRACTION_SYSTEM},
        {
            "role": "user",
            "content": f"Recent context:\n{recent_context}\n\nLatest user turn:\n{user_text}\n\nReturn the JSON array.",
        },
    ]


SUPERSEDE_SYSTEM = """You decide whether a NEW memory makes an OLD memory obsolete.
Return ONLY JSON: {"supersedes": true|false, "reason": "<short>"}.
"supersedes" is true only if the new statement updates, contradicts, or replaces
the old one (e.g. "allergic to peanuts" -> "outgrew peanut allergy"). If they
simply coexist, return false."""


def supersede_messages(old_content: str, new_content: str) -> list[dict]:
    return [
        {"role": "system", "content": SUPERSEDE_SYSTEM},
        {"role": "user", "content": f"OLD: {old_content}\nNEW: {new_content}"},
    ]


def compose_system_prompt(persona_prompt: str, member_name: str, member_role: str, memories: list[dict]) -> str:
    """Assemble the per-turn system prompt. Only THIS principal's memories enter."""
    if memories:
        mem_lines = "\n".join(f"- [{m['kind']}] {m['content']}" for m in memories)
        mem_block = f"On record in this context (use naturally, do not list verbatim):\n{mem_lines}"
    else:
        mem_block = "Nothing is on record in this context yet."

    return (
        f"{persona_prompt}\n\n"
        f"You are operating within a single isolated context: {member_name} ({member_role}). "
        f"You can only access information recorded in THIS context — never anything belonging to "
        f"another matter, client, or person. If asked about information that belongs to a different "
        f"context, state truthfully that you do not have access to it.\n\n"
        f"{mem_block}"
    )


def hitl_extract_messages(assistant_text: str) -> list[dict]:
    """Detect whether the assistant proposed an action needing approval."""
    sys = (
        "Decide if the assistant's reply proposes a concrete action that should "
        "require human approval (a reminder, a message draft, or a calendar event). "
        'Return ONLY JSON: {"action": null} if none, else '
        '{"action_type":"reminder|message_draft|calendar_event","payload":{...}}.'
    )
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": assistant_text},
    ]
