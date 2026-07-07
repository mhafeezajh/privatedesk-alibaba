"""Embedding helper. Same provider seam as the LLM wrapper."""
from __future__ import annotations

import litellm

from app.config import get_settings
from app.llm.client import _clean_model, _with_retry


async def embed(text: str) -> list[float]:
    s = get_settings()

    async def _call():
        resp = await litellm.aembedding(
            model=f"openai/{_clean_model(s.embedding_model)}",
            api_base=s.llm_base_url,
            api_key=s.llm_api_key,
            input=[text],
        )
        vec = resp["data"][0]["embedding"]
        # Guard against a degenerate/short vector slipping through on a 200: treat
        # it as retryable so _with_retry re-requests rather than persisting garbage.
        if not isinstance(vec, list) or len(vec) != s.embedding_dim:
            err = RuntimeError(
                f"degenerate embedding: got {len(vec) if isinstance(vec, list) else type(vec).__name__}, "
                f"expected {s.embedding_dim}"
            )
            err.status_code = 503  # type: ignore[attr-defined]
            raise err
        return vec

    return await _with_retry(_call)
