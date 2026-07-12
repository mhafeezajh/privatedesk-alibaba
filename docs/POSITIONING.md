# Positioning & FAQ — how PrivateDesk is different

Talking points for judges, investors, and customer Q&A. The recurring question is *"how is
this different from &lt;X&gt;?"* The honest, winning frame is almost always: **we're a different
layer, and we're complementary — not a replacement.**

---

## What PrivateDesk actually is (the layer)

PrivateDesk is **not** a model provider, a vector database, or a RAG framework. It is a
**governed, provably-isolated private-memory layer** that sits *on top of* a model backend. It
answers one question those tools leave to you:

> *How do I guarantee that one principal's (matter / patient / client / tenant) memory can
> **never** reach another's — and prove it to an auditor?*

## The thesis in one line

> "Bedrock/OpenAI are where models run; Pinecone is where vectors sit; PrivateDesk is the
> **isolation + memory + governance layer** that runs on top of any of them — and, uniquely, can
> run fully **local on open weights** in your own VPC or air-gapped."

## Four things that make us different

1. **Isolation is the product — structural, not a filter you can forget.** One physical vector
   namespace per principal, a single **chokepoint** that is *always* namespace-scoped, and a
   **guard test that fails the build** if anything crosses. Not "apply the right metadata filter
   on every query and hope."
2. **Sovereign & portable.** The same code runs on Qwen Cloud, on **local open-weight Qwen3
   (air-gapped, zero external calls)**, or in your own VPC. No hyperscaler lock-in. You own the
   database and the vector store.
3. **A purpose-built memory engine.** Accumulation, forgetting (supersession + decay), and
   bounded recall (salience+recency reranking) — measured at **100/100** on a behavior eval —
   not generic document retrieval.
4. **Governance for regulated *walls*.** Audit of every recall / write / isolation-block /
   approval, a **metadata-only oversight role** (compliance confirms the walls hold without
   seeing through them), human-in-the-loop, and a downloadable attestation.

*Depth signal:* we even isolate the **LLM prompt cache** — a shared surface most memory products
miss — by partitioning it per principal (not crudely disabling it), closing a cross-principal
timing side-channel. See [`CACHE-ISOLATION.md`](CACHE-ISOLATION.md).

---

## At a glance

| | AWS Bedrock | OpenAI Assistants / Memory | DIY (Pinecone + LangChain) | Mem0 / Zep | **PrivateDesk** |
|---|---|---|---|---|---|
| **Category** | Model serving + managed RAG | Hosted assistant + memory | Build-your-own kit | Memory-as-a-service | **Isolation + memory + governance layer** |
| **Isolation model** | Your job (metadata filters) | Your job (per-thread scoping) | Your job (namespaces/filters) | User/session scoping | **Structural: namespace-per-principal + chokepoint + guard test** |
| **Provable / attested?** | No | No | No | Not as a security guarantee | **Yes — audited `isolation_block`s + attestation + passing guard test** |
| **Runs on open weights / offline** | No (AWS only) | No | Depends on your models | Self-host yes; open-weight is on you | **Yes — local Qwen3, zero external calls** |
| **Vendor lock-in** | AWS | OpenAI | Mixed | Low | **None (provider-agnostic via LiteLLM)** |
| **Governance for ethical-wall/HIPAA** | Guardrails (content/PII) | Limited | Build it | Limited | **Audit + metadata-only oversight + HITL + report** |

---

## vs. AWS Bedrock

- **What it is:** managed access to foundation models + Knowledge Bases (managed RAG), Agents,
  and Guardrails (content/PII filtering).
- **Where it overlaps:** you *can* build multi-tenant memory with Knowledge Bases + metadata
  filtering.
- **How we differ:** that isolation is **your responsibility on every query** — one missing
  filter leaks. We make isolation structural and attested, add a real memory engine + ethical-wall
  governance, and run **outside AWS** (local/open-weight/your VPC).
- **Disarming line:** *"It's **and**, not **or** — swap one config line and PrivateDesk uses
  Claude **on Bedrock** as its backend. We're the layer above it."*

## vs. OpenAI Assistants API / ChatGPT Memory

- **What it is:** hosted assistants with threads, file search, tools; ChatGPT "memory" remembers
  across chats for consumers.
- **Where it overlaps:** persistent memory across sessions.
- **How we differ:** OpenAI's memory is **proprietary, cloud-only, and single-vendor**;
  multi-principal isolation is your app's job with no structural guarantee or audit. No
  self-host, no open weights, no compliance attestation. PrivateDesk is built for *regulated
  walls*, not consumer convenience — and it's portable and self-hostable.
- **Disarming line:** *"Great for a consumer assistant. Not something a firm can put a
  privileged matter behind — there's no provable wall, no audit, and the data leaves your
  boundary."*

## vs. DIY (Pinecone + LangChain, or similar)

- **What it is:** the assemble-it-yourself stack — an LLM + a vector DB + an orchestration
  framework.
- **Where it overlaps:** it's literally the primitives PrivateDesk is built from.
- **How we differ:** we ship the **opinionated, isolation-first architecture** so you don't
  hand-roll (and mis-secure) it: the chokepoint pattern, the guard test, the memory engine
  (forgetting/salience/bounded recall), the governance surface, and the run-anywhere provider
  seam. With DIY, isolation is a filter you must apply *everywhere* — the exact footgun we remove.
- **Disarming line:** *"You can build 70% of this in a weekend. The last 30% — proving the wall
  holds, keeping it green in CI, and the governance — is the part that actually ships to a
  regulated customer."*

## vs. Mem0 / Zep (dedicated memory layers)

- **What it is:** the closest *category* — memory layers for LLM apps (extract, store, retrieve
  memories; sessions/users; Zep adds a temporal knowledge graph). Both have open-source
  self-hostable editions.
- **Where it overlaps:** accumulation, retrieval, some forgetting, per-user scoping, self-host.
  Be honest: on raw memory sophistication (e.g. Zep's temporal graph) they are strong and mature.
- **How we differ:** our edge is **isolation as an attested security property** (chokepoint +
  guard test + audited isolation-blocks + a metadata-only oversight role) framed for **regulated
  verticals** where a cross-principal leak is a *compliance breach*, plus **open-weight
  sovereignty** (same code, fully local, zero external calls) and a **governance/HITL surface**.
  We're a *compliance-grade private memory product*, not just a memory API.
- **Disarming line:** *"Mem0/Zep scope memory by user; we make the wall between principals a
  **provable, audited** guarantee and wrap it in governance — the difference between 'memory
  that's organized' and 'memory a compliance officer will sign off on.'"*

---

## "Couldn't &lt;big company&gt; just build this?"

Yes — *anyone* can assemble similar plumbing. But then **you** own:
1. **Isolation correctness** — filter-based, leak-prone; our chokepoint + guard test prevent the
   failure by construction.
2. **The memory engine, governance, HITL, and attestation** — all of which you'd build and
   maintain.
3. **Lock-in** — to whichever cloud you built it on.

PrivateDesk packages the **isolation-first architecture + governance + portability** as the
default, with the wall **provable, not promised**. The moat isn't a single feature; it's the
*opinionated combination* and the guarantee.

---

## When **not** to reach for PrivateDesk (credibility matters)

- You just need **model access** → use Bedrock / the provider directly.
- You're building a **consumer** assistant with no isolation/compliance needs → ChatGPT memory is fine.
- You need a **mature temporal knowledge graph** today and isolation isn't a hard requirement → look at Zep.
- You have **one tenant** and no regulatory wall → you may not need the isolation layer at all.

**PrivateDesk shines when:** memory must be **private per principal**, the wall must be
**provable** (ethical wall, HIPAA, tenant isolation), and you need **sovereignty** (open weights /
your VPC / air-gapped) and an **auditable** governance trail.

---

## Cheat-sheet (memorize these)

- *"Different layer: we run **on** Bedrock/OpenAI/local, we don't replace them."*
- *"Isolation is **structural and attested**, not a filter you can forget."*
- *"Same code runs **fully local on open weights** — privacy isn't about where the bytes live."*
- *"Compliance confirms the walls hold **without seeing through them**."*
- *"The wall is **provable, not promised** — there's a guard test that fails the build if it leaks."*
