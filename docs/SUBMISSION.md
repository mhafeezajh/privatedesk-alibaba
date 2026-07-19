# Submission Packet — Qwen Cloud Global AI Hackathon

Everything the submission form asks for, assembled in one place. All URLs below are final.

---

## Track

**Track 1 — MemoryAgent.**

The project is a per-principal private memory layer for AI agents. It demonstrates the four
Track-1 behaviors — **accumulation, isolation, forgetting, bounded recall** — plus a
human-in-the-loop approval gate, in a legal "ethical wall" scenario.

---

## 1. Code repository (public + OSS license)

- **Repository URL:** https://github.com/mhafeezajh/privatedesk-alibaba
- **License:** MIT — [`LICENSE`](../LICENSE) at repo root (detectable by GitHub; shows in the
  **About** panel automatically once pushed).
- The repo contains **all** source (api, web), IaC (`infra/terraform`), assets (`docs/`), and
  run/deploy instructions ([`README.md`](../README.md), [`DEPLOY.md`](../DEPLOY.md)).

> ✅ Pushed. Secrets verified **not** committed (`.secrets.env`, `*.tfstate`, `generated/`,
> `terraform.tfvars` are all git-ignored).
> ⚠️ **Before submitting:** confirm the repo is set to **Public** (Settings → General → Change
> visibility) and that the **About** panel shows the **MIT** license badge.

---

## 2. Text description (features & functionality)

> **PrivateDesk MemoryAgent** gives every AI principal its own private, persistent,
> isolated memory. In the reference build — a law firm running several **matters** — the wall
> between one matter's memory and another's *is* the profession's **ethical wall**, and we make
> it provable rather than promised.
>
> **What it does**
> - **Accumulation** — facts told to a matter are distilled into durable memories and recalled,
>   unprompted, in later sessions (persisted in PostgreSQL + a Qdrant vector store, not just
>   chat history).
> - **Isolation** — each matter has an opaque, server-minted namespace. All vector retrieval
>   flows through a single chokepoint that is *always* namespace-scoped, so one matter's
>   assistant physically cannot read another's memory. Attempts are logged as `isolation_block`
>   and covered by an automated guard test. Isolation extends even to the **LLM prompt cache** —
>   partitioned per principal so a shared provider cache can't become a cross-matter timing
>   side-channel (see [`CACHE-ISOLATION.md`](CACHE-ISOLATION.md)).
> - **Forgetting** — superseding facts are auto-detected and the old ones retired; an expiry +
>   low-salience sweep prunes stale memory on demand.
> - **Bounded recall** — with 115 memories on one matter, a similarity + salience + recency
>   reranker injects only the top few (de-duplicated) into the prompt, under a token budget.
> - **Human-in-the-loop** — the assistant *drafts* actions (reminders, message drafts, calendar
>   events); a supervising human approves before anything is "done."
>
> **How it's built.** A FastAPI backend (memory engine, LiteLLM provider seam, the Qdrant
> isolation chokepoint) serves a Next.js "cockpit" that visualizes the memory store, the live
> recall trace, the audit log, and the ethical wall side by side. The **same code** runs on
> **Qwen Cloud (DashScope)** — `qwen-plus`, `qwen3-max`, `text-embedding-v4` — or fully local on
> open-weight **Qwen3 via Ollama**, selected by a single environment variable. Privacy here
> isn't about where the bytes live; it's **isolation, open weights, and never training on your
> data** — and Qwen makes all three possible.
>
> **What Qwen powers** (not just "an LLM call"). `qwen-plus` — reasoning grounded in *this*
> principal's recalled memory, plus the **structured-JSON** output that extracts memories, renders
> the isolation-guard verdict, and drafts the human-in-the-loop actions; `qwen3-max` — flagship
> marquee turns; `text-embedding-v4` (1024-d, multilingual) — the embeddings that make memory
> recallable by *meaning*. The LLM prompt cache is partitioned per principal so a shared cache
> can't leak across the wall.
>
> **Deployment.** One `terraform apply` stands up the whole stack on **Alibaba Cloud ECS**
> (VPC, security group, EIP), ships the code, and seeds the demo — reachable, healthy, and
> provably isolated.

*(Longer version: [`README.md`](../README.md). Deep dive: [`TECHNICAL-ARCHITECTURE.md`](TECHNICAL-ARCHITECTURE.md).)*

### How is this different from AWS Bedrock / OpenAI / a DIY RAG stack?

Different **layer**, and complementary — not a replacement. Bedrock/OpenAI are where models run;
Pinecone is where vectors sit. PrivateDesk is the **isolation + memory + governance layer** that
runs *on top of* any of them (swap one config line and it uses Claude on Bedrock, Qwen Cloud, or
**fully local open-weight Qwen3**). The difference that matters: on those platforms, multi-tenant
isolation is **your job on every query** — one missing metadata filter leaks. PrivateDesk makes
the wall **structural and provable** (one namespace per principal → a single chokepoint → a guard
test that fails the build if anything crosses), adds a real memory engine (accumulation /
forgetting / bounded recall) and ethical-wall governance (audit, metadata-only oversight, HITL,
attestation), and runs in **your own VPC or air-gapped** with no hyperscaler lock-in.

→ Full competitive breakdown (vs. Bedrock, OpenAI Assistants/Memory, DIY Pinecone+LangChain,
Mem0/Zep), with a comparison matrix and Q&A talking points: [`POSITIONING.md`](POSITIONING.md).

---

## 3. Architecture diagram

![PrivateDesk MemoryAgent architecture — Next.js frontend → FastAPI backend → PostgreSQL / Qdrant / Redis, with a LiteLLM seam to Qwen Cloud (DashScope) or local Ollama](architecture.png)

*Browser → Next.js frontend → FastAPI backend → PostgreSQL / Qdrant / Redis, with the LiteLLM
seam out to **Qwen Cloud (DashScope)** or local Ollama. Source: [`architecture.svg`](architecture.svg).*
- **Supporting flow diagrams:** [write path](flow_write_path.svg), [recall path](flow_recall_path.svg),
  [isolation](flow_isolation.svg), [forgetting](flow_forgetting.svg).
- **Text + ASCII topology:** [`TECHNICAL-ARCHITECTURE.md`](TECHNICAL-ARCHITECTURE.md) §2.

---

## 4. Proof of Alibaba Cloud deployment

**(a) Code files demonstrating use of Alibaba Cloud services & APIs** (link these in the form):

| Alibaba Cloud service | Code file | What it shows |
|---|---|---|
| **Qwen Cloud / DashScope** (Model Studio) — LLM API | [`api/app/llm/client.py`](../api/app/llm/client.py) | All completions/streaming call the DashScope OpenAI-compatible endpoint via LiteLLM |
| **DashScope embeddings** (`text-embedding-v4`) | [`api/app/memory/embeddings.py`](../api/app/memory/embeddings.py) | 1024-d embeddings from DashScope |
| **DashScope endpoint + seam** | [`api/app/config.py`](../api/app/config.py) | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`, model IDs |
| **Alibaba Cloud ECS / VPC / EIP** — infra APIs | [`infra/terraform/compute.tf`](../infra/terraform/compute.tf), [`network.tf`](../infra/terraform/network.tf) | Provisions the ECS instance, VPC, security group, EIP via the `alicloud` provider |

**(b) Short proof-of-deployment recording** (separate from the demo video):

- **URL:** https://youtu.be/erLKMc1akzI
- **Script:** [`VIDEO-SCRIPT-ALIBABA-PROOF.md`](VIDEO-SCRIPT-ALIBABA-PROOF.md) (~60–90 s)
- It shows the ECS console (running instance, Singapore region, public IP **47.236.30.110**),
  an SSH session with all containers up, and `/health` returning `"provider":"Qwen Cloud
  (DashScope)","llm_ok":true` — i.e. the backend is live on Alibaba Cloud and calling Qwen.

---

## 5. Demo video (~3 minutes, public)

- **URL:** https://youtu.be/SHQ_RtlwLyA (YouTube, set **public**)
- **Script:** [`demo-video-script.md`](demo-video-script.md) — shot-by-shot, timed to <3:00,
  built around the isolation "money shot."
- Recorded against the **live Alibaba Cloud deployment** at http://47.236.30.110:3000.

---

## 6. Optional — Blog / social post (Blog Post Prize)

- **URL:** ⟨BLOG_URL⟩ (optional)
- Suggested angle: "Building a provable ethical wall for AI memory on Qwen Cloud" — the
  isolation chokepoint, the cloud⇄local seam, and the one-command Alibaba Cloud IaC, including
  the real debugging journey (the half-indexed-seed bug and the durable-upsert fix).

---

## Submission checklist

- [ ] **Public repo** URL with **MIT** license visible in About — https://github.com/mhafeezajh/privatedesk-alibaba
- [ ] **Text description** — §2 above (paste into the form)
- [ ] **Architecture diagram** — `docs/architecture.png` attached / linked
- [ ] **Alibaba Cloud proof — code file link** — `api/app/llm/client.py` (+ `infra/terraform/`)
- [ ] **Alibaba Cloud proof — short video** — https://youtu.be/erLKMc1akzI
- [ ] **Demo video (~3 min, public)** — https://youtu.be/SHQ_RtlwLyA
- [ ] **Track** — Track 1 (MemoryAgent)
- [ ] Secrets verified **not** committed (`.secrets.env`, `*.tfstate`, `generated/` ignored)
- [ ] `/health` on the live box returns `llm_ok: true` at recording time
- [ ] (Optional) Blog post — ⟨BLOG_URL⟩

---

## Live endpoints (as deployed)

| | |
|---|---|
| App | http://47.236.30.110:3000 |
| Health | http://47.236.30.110:8000/health |
| Region / instance | Alibaba Cloud `ap-southeast-1` (Singapore) · `ecs.u1-c1m4.large` (2 vCPU / 8 GB) |
| Isolation proof | `ssh -i infra/terraform/generated/privatedesk.pem root@47.236.30.110 'cd privatedesk-memoryagent && docker compose exec -T api pytest -q tests/test_isolation.py'` |

> ## ⚠️ The box is currently STOPPED (to stop pay-as-you-go charges)
>
> The ECS instance is stopped in StopCharging mode, so **the URLs above will not respond right
> now**. This is deliberate cost control — but it means:
>
> 1. **Before recording either video**, run `make infra-start` (boots at the *same* IP in ~1–2 min;
>    the app auto-restarts). Verify `/health` → `"llm_ok": true`, then record.
> 2. **Before you submit / while judging is open**, run `make infra-start` and **leave it running**
>    — a judge clicking a dead link is a lost submission. At ~$0.10/hr (2 vCPU/8 GB) a week of
>    judging is only a few dollars.
> 3. `make infra-stop` when idle; `make infra-down` to destroy everything once judging closes.
>
> If you'd rather not depend on a live box at all, the **videos + repo are self-sufficient** —
> the live URL is a bonus, not a requirement of the rules.
