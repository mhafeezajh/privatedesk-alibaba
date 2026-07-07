"""The one place model calls happen.

Everything goes through here so the cloud/local swap is a config change, not a
code change. `_clean_model` strips the `dashscope/` or `ollama/` prefix before
the HTTP call (LiteLLM's openai-compatible route wants the bare model name).
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import litellm

from app.config import get_settings

litellm.drop_params = True  # tolerate provider-specific kwargs differences

_RETRYABLE = (429, 500, 502, 503, 504)


def _clean_model(model: str) -> str:
    for prefix in ("dashscope/", "ollama/"):
        if model.startswith(prefix):
            return model[len(prefix):]
    return model


def _route(model: str) -> str:
    # openai-compatible route works for both DashScope compatible-mode and Ollama /v1
    return f"openai/{_clean_model(model)}"


async def _with_retry(coro_factory, attempts: int = 4):
    delay = 1.0
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return await coro_factory()
        except litellm.exceptions.RateLimitError as e:  # type: ignore[attr-defined]
            last_exc = e
        except Exception as e:  # noqa: BLE001 — surface after retries
            status = getattr(e, "status_code", None)
            if status not in _RETRYABLE:
                raise
            last_exc = e
        await asyncio.sleep(delay)
        delay *= 2
    assert last_exc is not None
    raise last_exc


async def complete(messages: list[dict], *, headline: bool = False, temperature: float = 0.4) -> str:
    """Non-streaming completion. Uses the headline model for marquee turns."""
    s = get_settings()
    model = s.headline_model if headline else s.reasoning_model

    async def _call():
        return await litellm.acompletion(
            model=_route(model),
            api_base=s.llm_base_url,
            api_key=s.llm_api_key,
            messages=messages,
            temperature=temperature,
        )

    resp = await _with_retry(_call)
    return resp["choices"][0]["message"]["content"] or ""


async def complete_json(messages: list[dict]) -> dict | list:
    """Completion constrained to JSON. Strips accidental code fences."""
    raw = await complete(messages, temperature=0.1)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # last-ditch: pull the outermost JSON object/array
        start = min((cleaned.find("{"), cleaned.find("[")), key=lambda x: (x < 0, x))
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        if 0 <= start <= end:
            return json.loads(cleaned[start : end + 1])
        raise


async def stream(messages: list[dict], *, headline: bool = False) -> AsyncIterator[str]:
    """Token stream for the chat endpoint (SSE)."""
    s = get_settings()
    model = s.headline_model if headline else s.reasoning_model
    resp = await litellm.acompletion(
        model=_route(model),
        api_base=s.llm_base_url,
        api_key=s.llm_api_key,
        messages=messages,
        temperature=0.5,
        stream=True,
    )
    async for chunk in resp:
        delta = chunk["choices"][0]["delta"].get("content")
        if delta:
            yield delta
