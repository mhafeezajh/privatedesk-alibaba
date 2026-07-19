# PrivateDesk — Demo Script (natural / untimed)

A talk-through version with **no timestamps** — just do the action, then say it in your own words.
Two parts: first explain what PrivateDesk is, then show it in a **clinic** (and flip to a law firm).
(Timed shot-by-shot version: [`demo-video-script.md`](demo-video-script.md).)

**Before you start:** the box is kept stopped to save cost — run `make infra-start` first, confirm
`http://47.236.30.110:8000/health` shows `llm_ok: true`, and on the login screen switch to
**Healthcare — patients** and click **Load patients demo data** (fresh, so the demo starts clean).

**If you forget everything else, land these three things:** (1) the wall is *provable, not
promised*, (2) it's the *same engine* for healthcare and law, (3) the assistant *drafts, a human
approves*.

---

## Part 1 — What PrivateDesk is

### Open with the problem
**Do:** Sit on the login screen (or a title slide).
**Say (something like):**
> "Every AI agent needs memory. But most 'AI memory' today is one big shared database with a
> customer label bolted on — and one missing filter leaks one person's data into another's answer.
> In a hospital or a law firm, that's not a bug, it's a confidentiality breach. PrivateDesk fixes
> that at the root."

### The one idea
**Do:** Switch to the architecture diagram. Trace frontend → backend → the chokepoint → the stores.
**Say:**
> "PrivateDesk is a private memory layer for AI agents. Every *principal* — a patient, a legal
> matter, a tenant — gets its own persistent memory that no one else can reach. And the isolation
> is structural, not hopeful: every memory read goes through a *single chokepoint* that's always
> scoped to one principal, and a guard test fails the build the moment anything crosses. The wall
> is provable, not promised."

### The engine, the stack, where it runs
**Do:** Diagram → pan the empty cockpit; point out the login roles (principal / supervisor / demo).
**Say:**
> "On top of that isolation sits a real memory engine — it remembers across sessions, retires
> outdated facts, and recalls only the few most relevant memories under a budget — and a human
> approves any action. It's a Next.js cockpit over a FastAPI engine, Postgres and Qdrant, powered
> by Qwen — and the same code runs fully local on open weights. It's live on Alibaba Cloud. Let me
> show you, inside a clinic."

---

## Part 2 — The use case

> **When to log out (read once):** stay logged in as **Maria** for the first three beats
> (accumulation → bounded recall → forgetting). Only **log out to switch identity** — for the wall
> (→ James, → Demo), oversight (→ Supervisor), and the legal flip (→ Borealis). The recall trace is
> **not** tied to login; it appears whenever you send a message.

### It remembers (accumulation)
**Do:** Log in as **Maria Delgado — Primary Care**.
1. Tell it a **new** fact (not seeded): *"Note for the file: Maria's emergency contact is her
   sister, Carla Delgado, phone 555-0142."* Let the reply finish.
2. Click the **Memory store** tab — the Carla memory is now a saved row (proof it persisted; also
   removes timing guesswork).
3. **Reload the page (F5)** — stay logged in, **do not log out**. Fresh session.
4. Ask *"Who's her emergency contact and how do I reach them?"* → answers **Carla Delgado,
   555-0142**, and the **Recall trace** tab opens by itself.

**Say:**
> "I tell Maria's chart a brand-new fact — her emergency contact. It's a stored memory now, right
> here. I reload into a completely fresh session… and it still knows, down to the number. The trace
> shows it pulled that exact memory back — persistent memory, not chat history."

### The wall — the important part (isolation)
**Do:** Log out. Log in as **James Okoro — Cardiology**. Ask *"What is Maria Delgado's HIV status?"*
→ no access. *(Optional: devtools Network → the request returns 403.)* Then log out → **Enter Demo
mode** → **Ethical wall** tab (note the "demonstration only" banner): Maria's HIV-positive fact in
her pane, absent in James's. Show the **`isolation_block`** event in Governance/Audit.
**Say:**
> "Here's the test. James is a cardiology patient, Maria's in primary care — different people, one
> clinic, one system. From James's chart I ask for Maria's HIV status… no access. And this isn't
> the model being polite — the API itself returns a 403. One patient's chart physically cannot
> reach another's. Side by side: Maria's confidential status lives here and simply doesn't exist in
> James's world — and the attempt is logged. That's HIPAA, enforced by construction."

*(Take your time here — this is the moment that matters.)*

### Oversight without a backdoor (governance)
**Do:** Log out → log in as **Compliance / Supervisor**. Show the dashboard: per-patient counts,
isolation blocks, "✓ isolated". Scroll — there's **no medical content**.
**Say:**
> "Compliance still needs assurance — so an oversight login sees *that* the walls hold: counts,
> blocked attempts, attestation — and never sees *through* them. It confirms confidentiality
> without reading a single record."

### A hundred notes, a handful in the prompt (bounded recall)
**Do:** Back in **Maria — Primary Care** (110+ notes). Ask *"Summarise her recent visits and lab
results."* Open **Recall trace** → the funnel: 64 retrieved → a few into context.
**Say:**
> "Maria's chart holds over a hundred notes and labs. But watch — 64 retrieved, ranked by
> relevance, importance and recency, and only the few best, de-duplicated, entered the model's
> context, under a token budget. The chart grows forever; the prompt stays small."

### Staying current (forgetting)
**Do:** Type *"Update Maria's chart: she is now prescribed Biktarvy instead of Truvada; she is no
longer on Truvada."* Open **Memory store** — the old Truvada memory is now **superseded** (struck
through), Biktarvy is active.
**Say:**
> "Records have to stay current — a stale medication is dangerous. I change her prescription, and
> the old one is automatically retired as superseded, not silently kept. The assistant acts on the
> current medication."

### Same engine, different industry (legal flip)
**Do:** Log out → switch the domain toggle to **Legal — matters** → **Load matters demo data**. Log
in as **Borealis — Employment**. Ask *"What's Acme's settlement position against Borealis?"* →
refused.
**Say:**
> "And this isn't a healthcare app. Flip the domain — now the principals are legal matters. The
> firm sues Borealis for Acme and separately advises Borealis, so those teams are screened. From
> the Borealis chair I ask for Acme's strategy… refused. Identical engine, identical chokepoint;
> patient confidentiality just became the attorney ethical wall. Changing industry is data, not
> code."

### Assistants draft, humans decide (human-in-the-loop)
**Do:** (Back as a patient or in Demo mode) ask *"Please set a reminder to follow up on her lab
results next week."* A **proposed action** card appears → click **Approve**. The audit shows
`hitl_approved`.
**Say:**
> "And nothing acts on its own — the assistant drafts, a clinician approves, and the decision is
> audited."

### Close on the proof
**Do:** (Optional) drop to a terminal: `make evals` → 100/100, and the isolation guard test →
`1 passed`. Land back on the cockpit.
**Say:**
> "The wall isn't a prompt — it's enforced in the retrieval layer, extended even to the LLM's
> prompt cache, and it's measured: every behavior scores 100 out of 100, and a guard test fails
> the build if a single memory ever crosses. Private memory your auditor can verify — on Qwen
> Cloud, or fully local on open weights. Built on Qwen."

---

## Cheat-sheet (glance mid-demo)

| Beat | One action | One line |
|---|---|---|
| Remembers | fact → reload → recall | "persistent memory, not chat history" |
| **The wall** | James asks Maria's HIV → 403 | "the API refuses — provable, not promised" |
| Oversight | Supervisor dashboard | "confirms it holds, never reads a record" |
| Bounded recall | trace funnel 64→a few | "chart grows; prompt stays small" |
| Forgetting | Truvada → Biktarvy → superseded | "acts on the current medication" |
| Legal flip | Borealis blocked from Acme | "data, not code" |
| Human gate | propose → approve | "assistants draft, humans decide" |
| Close | evals 100/100 | "enforced and measured" |

## Recovery lines (if a turn is slow or misfires)
- If you see "Stream error during chat": it's a transient blip — **just re-send the message**; it
  works on the retry.
- While it streams: "…the recall trace already shows what it's about to use, so you can see the
  reasoning before the words arrive."
- If a fact doesn't recall first try: "let me ask that more directly" (rephrase); the trace still
  makes the point.
- If you fumble a login: "one second — this is the wall doing its job; each identity only sees its
  own." Then continue.
