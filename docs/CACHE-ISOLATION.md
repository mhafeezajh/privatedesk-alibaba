# Prompt-cache isolation — a second-order leak, closed

Most "AI memory" products stop at scoping the *database*. But there's a subtler shared surface:
the **LLM provider's prompt cache**. This note is the threat model and the mitigation PrivateDesk
ships.

## The concern (stated precisely)

To cut cost and latency, LLM providers cache **prompt prefixes**:
- **Anthropic** — explicit `cache_control` breakpoints.
- **OpenAI / DashScope (Qwen)** — implicit, content-hash based.

Within a single deployment, **all principals share one provider API key**, so they share one
cache. Two questions follow:

1. **Can principal B receive principal A's private content from the cache?**
   **No.** A cache *hit* only skips recomputation of a prefix **B itself already sent** — it
   returns the same tokens B would have gotten anyway. The cache never injects A's text into B's
   prompt. B's prompt only ever contains B's own recalled memories (enforced by the isolation
   chokepoint). So there is no direct content-transfer path.

2. **Can B *infer* something about A via the cache?**
   **Yes — a timing side-channel.** If B submits a prompt prefix and gets a suspiciously fast
   response (a cache hit), B can infer that *someone else* recently submitted that same prefix.
   That's **membership inference**: B learns A asked about a specific thing, without ever seeing
   A's data. For an ethical wall or HIPAA, leaking *"the other side researched X"* is itself a
   confidentiality breach. (This class of attack on shared prompt caches is documented in the
   literature.)

> So the real risk isn't content theft — it's a **timing/membership side-channel** across
> principals who share one provider cache.

## Why "just disable caching" is the wrong answer

Disabling caching removes the side-channel, but throws away the cost and latency benefit — which
on a long, static system prefix (persona + instructions + recalled memories) is substantial. We
want isolation **and** the cache.

## The fix: partition the cache by principal

Prepend an **opaque, per-principal token** to the cached prefix, derived from the principal's
**namespace** (which is secret and resolved server-side, never exposed to a client):

```
[cache-partition:<HMAC(session_secret, namespace)>] (internal; ignored by the model)
<the normal system prompt…>
```

Because the token is part of the cached prefix:

| Property | Result |
|---|---|
| Same principal, many turns | identical token → **cache hits** → cost/latency preserved ✅ |
| Principal A vs principal B | different token → prefixes **can never match** → no cross-principal hit ✅ |
| B tries to probe A's prefix | B can't reconstruct A's token (unguessable, keyed by `SESSION_SECRET`) → **no timing inference** ✅ |

Caching is kept *within* each principal and eliminated *across* principals — exactly the wall,
extended to the cache layer. Implemented in
[`api/app/llm/cache_isolation.py`](../api/app/llm/cache_isolation.py); applied to the chat prompt
in [`api/app/routers/chat.py`](../api/app/routers/chat.py).

## Modes (env `PROMPT_CACHE_MODE`)

| Mode | Behavior | Use when |
|---|---|---|
| **`partitioned`** *(default)* | per-principal salt on the cached prefix | normal multi-principal deployments — safe **and** fast |
| **`off`** | a fresh nonce per call → nothing is ever a cache hit | maximum-privacy / highly-adversarial tenants (accepts higher cost + latency) |
| **`shared`** | no token → provider default | a genuinely **single-tenant** deployment where there's no cross-principal cache to worry about |

Visible at runtime in `GET /health` → `"prompt_cache_mode"`.

## Defense in depth — and the sovereign path

- Provider caches are already **scoped to your API key/organization**, so there is no cross-
  *customer* (cross-org) leakage to begin with; partitioning addresses the residual **intra-account,
  cross-principal** side-channel.
- On the **local / open-weight path** (Ollama / self-hosted), the KV-cache lives **inside your own
  process and boundary** — you own the cache policy entirely, and for air-gapped tenants the
  concern is moot. This is another reason the "runs fully local on open weights" story matters.

## Why this is a differentiator

Scoping the vector store is table stakes. Recognizing that the **LLM prompt cache** is a shared
surface — and partitioning it per principal rather than crudely disabling it — is the kind of
second-order isolation a compliance reviewer for a law firm or hospital will actually probe.
PrivateDesk closes it by construction, with a one-line config to dial privacy vs. cost.
