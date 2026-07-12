"""Prompt-cache isolation.

LLM providers cache prompt *prefixes* (Anthropic explicit cache, DashScope/OpenAI implicit
content-hash cache) to cut cost and latency. Within ONE API key the cache is shared, which
creates a subtle cross-principal risk — not raw content injection (a cache hit only returns the
tokens you already sent), but a **timing side-channel / membership inference**: principal B could
detect that principal A recently submitted a given prompt prefix by measuring the faster cache
hit. For an ethical-wall / HIPAA product that is still a confidentiality leak.

The fix is NOT to disable caching (that kills the cost/perf win). It is to **partition** the cache
by principal: prepend an opaque, per-principal token — derived from the (secret, server-side)
namespace — to the cached prefix. Then:

  - Caching still works WITHIN a principal (same token across their turns → cache hits). ✅ perf
  - A's and B's prefixes can never match (different token) → no cross-principal cache hit, and
    B cannot reconstruct A's salted prefix to probe it (the token is unguessable). ✅ isolation

Modes (env PROMPT_CACHE_MODE):
  - "partitioned" (default): per-principal salt — safe + fast.
  - "off": a fresh nonce per call — caching is effectively disabled (max privacy, higher cost).
  - "shared": no token — provider default; only safe for a genuinely single-tenant deployment.
"""
from __future__ import annotations

import hashlib
import hmac
import uuid

from app.config import get_settings


def cache_token(namespace: str) -> str:
    """The per-principal cache-partition token for the current mode ("" = no partitioning)."""
    mode = get_settings().prompt_cache_mode
    if mode == "shared":
        return ""
    if mode == "off":
        return uuid.uuid4().hex  # unique per call → never a cache hit
    # "partitioned": stable per principal, unguessable (keyed by SESSION_SECRET)
    secret = get_settings().session_secret.encode()
    return hmac.new(secret, namespace.encode(), hashlib.sha256).hexdigest()[:16]


def with_boundary(system_prompt: str, namespace: str) -> str:
    """Prepend the cache-partition boundary so the provider's prompt-prefix cache is scoped to
    this principal. The token is internal — the model is told to ignore it."""
    token = cache_token(namespace)
    if not token:
        return system_prompt
    return f"[cache-partition:{token}] (internal routing token — ignore)\n{system_prompt}"
