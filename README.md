# PrivateDesk MemoryAgent

**A legal matter memory agent where every matter has a private, isolated, persistent
assistant — and the ethical wall between matters is provable.** Built for the Qwen Cloud Global AI
Hackathon, Track 1 (MemoryAgent). The exact same code runs on Qwen Cloud
(DashScope) or fully local on Ollama-served open-weight Qwen3 — because privacy
isn't about *where the bytes live*. It's three things: **isolation, open weights,
and never training on your data.** Qwen makes all three possible.

This repo demonstrates the four behaviors Track 1 scores:

1. **Accumulation** — a fact added to a matter is recalled, unprompted, in a later session.
2. **Isolation** — one matter's assistant cannot access another matter's memory (the ethical wall), and the inspector shows the stores are physically separate.
3. **Forgetting** — superseded facts are deprecated, expired facts swept, low-salience memories pruned.
4. **Bounded recall** — with 100+ stored memories, only the top few relevant ones enter the prompt, under a token budget.

Plus a **human-in-the-loop** gate: the agent proposes actions; a human approves.

---

## Architecture (one glance)

```
Next.js (chat + inspector)  ──HTTP/SSE──>  FastAPI
                                             ├─ memory engine (write / read / forget)
                                             ├─ isolation chokepoint  ──> Qdrant (per-matter)
                                             ├─ LiteLLM  ──> Qwen Cloud (DashScope)  [PRIMARY]
                                             │            └─> Ollama (open weights)   [LOCAL ALT]
                                             ├─ PostgreSQL (identity, memories, audit)
                                             └─ Redis (sessions)
```

The single seam that swaps cloud ⇄ local is the presence of `DASHSCOPE_API_KEY`.
Nothing else in the code branches on it.

---

## Run it — Cloud path (Qwen Cloud / DashScope)

1. Get a DashScope key from Alibaba Cloud Model Studio (enable **Free Quota Only**).
2. Configure env:
   ```bash
   cp .env.example .env
   # set DASHSCOPE_API_KEY=sk-...   (leave the LLM_* cloud block as-is)
   ```
3. Bring up the stack:
   ```bash
   docker compose up --build
   ```
4. Verify the provider is live (one real completion + one real embedding):
   ```bash
   curl localhost:8000/health
   # -> {"provider":"Qwen Cloud (DashScope)","llm_ok":true,"embedding_dim_live":1024,...}
   ```
5. Seed the demo (3 matters incl. an adverse pair + 100+ discovery memories on the litigation matter):
   ```bash
   curl -X POST localhost:8000/api/demo/seed -H 'content-type: application/json' -d '{"scenario":"legal"}'
   ```
6. Open the web UI at `http://localhost:3000` (see `web/`).

## Run it — Local path (Ollama, open weights)

No code changes — only env:
```bash
ollama serve
ollama pull qwen3:8b && ollama pull nomic-embed-text
# in .env: empty DASHSCOPE_API_KEY, uncomment the LOCAL_* block in .env.example
docker compose up --build
curl localhost:8000/health   # -> {"provider":"Local (Ollama)", ...}
```

---

## The isolation guarantee (and how to verify it)

Every vector read goes through **one** function — `app/memory/qdrant_client.py:search()` —
which always scopes to a single matter's namespace. No other module touches
Qdrant. The guard test proves the wall holds across 100+ seeded memories:

```bash
# with the stack up and a provider reachable:
pytest -q api/tests/test_isolation.py
```

A query in one matter never returns another matter's memory id. This test, exported, is the
"isolation attestation" — the artifact a security review can rely on.

---

## Key endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/session/start` | begin a session for a matter |
| `POST /api/chat` | SSE chat: recall → compose → stream → async memory write → HITL detect |
| `GET /api/members` | matter switcher (matters are the principals) |
| `GET /api/inspector/memories` | a matter's memory store (status + salience) |
| `GET /api/inspector/audit` | audit log incl. `isolation_block` events |
| `POST /api/inspector/maintenance` | run forgetting sweep live |
| `GET /api/actions/pending` · `POST /api/actions/{id}/approve|reject` | human-in-the-loop |
| `POST /api/demo/seed` | seed personas + 100+ memories |

---

## What's intentionally NOT here

The full PrivateDesk dashboard, email/finance/travel modules, federation, native
apps, billing, and multi-household tenancy are deliberately out of scope for the
hackathon. This repo is the memory engine and the proof.

## License

MIT — see `LICENSE`.
