# PrivateDesk — Demo Script (natural / untimed)

A talk-through version with **no timestamps** — just do the action, then say it in your own words.
Two parts: first explain what PrivateDesk is, then show it in a law firm (and a clinic).
(Timed shot-by-shot version: [`demo-video-script.md`](demo-video-script.md).)

**Before you start:** the box is kept stopped to save cost — run `make infra-start` first, confirm
`http://47.236.30.110:8000/health` shows `llm_ok: true`, and on the login screen load the
**Legal — matters** demo data.

**If you forget everything else, land these three things:** (1) the wall is *provable, not
promised*, (2) it's the *same engine* for law and healthcare, (3) the assistant *drafts, a human
approves*.

---

## Part 1 — What PrivateDesk is

### Open with the problem
**Do:** Sit on the login screen (or a title slide).
**Say (something like):**
> "Every AI agent needs memory. But most 'AI memory' today is one big shared database with a
> customer label bolted on — and one missing filter leaks one client's data into another's answer.
> In a law firm or a hospital, that's not a bug, it's a confidentiality breach. PrivateDesk fixes
> that at the root."

### The one idea
**Do:** Switch to the architecture diagram. Trace frontend → backend → the chokepoint → the stores.
**Say:**
> "PrivateDesk is a private memory layer for AI agents. Every *principal* — a legal matter, a
> patient, a tenant — gets its own persistent memory that no one else can reach. And the isolation
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
> show you, inside a law firm."

---

## Part 2 — The use case

### It remembers (accumulation)
**Do:** Log in as **Acme — Litigation**. Tell it a **new** fact (one that isn't seeded): *"Note for
the file: our lead paralegal on this matter is Marcus Bell, extension 4471."* Wait ~2 seconds, then
**reload the page** (fresh session). Ask *"Who's our paralegal here and how do I reach them?"* → it
answers **Marcus Bell, ext 4471**. Open the **Recall trace** tab.
**Say:**
> "I tell the Acme matter a brand-new fact — our paralegal, Marcus Bell — then start a fresh
> session, and it still knows, right down to his extension. That became persistent memory, not chat
> history. The trace shows exactly which memory it pulled back."

### The wall — the important part (isolation)
**Do:** Log out. Log in as **Borealis — Employment**. Ask the *same* question: *"What's Acme's
settlement position against Borealis?"* → no access. *(Optional: devtools Network → the request
returns 403.)* Then log out → **Enter Demo mode** → **Ethical wall** tab (note the "demonstration
only" banner): $4.2M in the Acme pane, absent in Borealis's. Show the **`isolation_block`** event
in Governance/Audit.
**Say:**
> "Here's the test. The firm sues Borealis for Acme — and separately advises Borealis. Those teams
> must be screened. So I log in as the Borealis attorney and ask for Acme's strategy… no access.
> And this isn't the model being polite — the API itself returns a 403. One principal's login
> physically cannot reach another's memory. Side by side: Acme's privileged $4.2 million ceiling
> lives here, and simply doesn't exist in Borealis's world — and the attempt is logged."

*(Take your time here — this is the moment that matters.)*

### Oversight without a backdoor (governance)
**Do:** Log out → log in as **Compliance / Supervisor**. Show the dashboard: per-matter counts,
isolation blocks, "✓ isolated". Scroll — there's **no memory content**.
**Say:**
> "Compliance still needs assurance — so an oversight login sees *that* the walls hold: counts,
> blocked attempts, attestation — and never sees *through* them. Oversight isn't a backdoor."

### A hundred memories, a handful in the prompt (bounded recall)
**Do:** Back in **Acme — Litigation** (115 memories). Ask *"What discovery do we have on the
supply-contract timeline?"* Open **Recall trace** → the funnel: 64 retrieved → a few into context.
**Say:**
> "This matter holds over a hundred discovery memories. But watch — 64 retrieved, ranked by
> relevance, importance and recency, and only the few best, de-duplicated, entered the model's context, under a
> token budget. The store grows forever; the prompt stays small."

### Staying current (forgetting)
**Do:** Type *"Update: the board raised the settlement ceiling to $5M."* Open **Memory store** —
the old $4.2M is now **superseded** (struck through), $5M is active.
**Say:**
> "Memory has to stay current. I raise the ceiling, and the old figure is automatically retired as
> superseded — not silently kept. The assistant acts on the new truth."

### Same engine, different industry (healthcare)
**Do:** Log out → switch the domain toggle to **Healthcare — patients** → **Load patients demo
data**. Log in as **James Okoro — Cardiology**. Ask *"What is Maria Delgado's HIV status?"* →
refused.
**Say:**
> "And this isn't a legal app. Flip the domain — now the principals are patients. On James's chart
> I ask for another patient's HIV status… refused. Identical engine, identical chokepoint; the
> ethical wall just became patient confidentiality. Changing industry is data, not code."

### Assistants draft, humans decide (human-in-the-loop)
**Do:** Ask *"Please set a reminder to file the motion to exclude next Friday."* A **proposed
action** card appears → click **Approve**. The audit shows `hitl_approved`.
**Say:**
> "And nothing acts on its own — the assistant drafts, a human approves, and the decision is
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
| **The wall** | Borealis asks Acme → 403 | "the API refuses — provable, not promised" |
| Oversight | Supervisor dashboard | "sees *that* it holds, never *through* it" |
| Bounded recall | trace funnel 64→a few | "store grows; prompt stays small" |
| Forgetting | raise ceiling → superseded | "acts on the new truth" |
| Healthcare | James blocked from Maria | "data, not code" |
| Human gate | propose → approve | "assistants draft, humans decide" |
| Close | evals 100/100 | "enforced and measured" |

## Recovery lines (if a turn is slow or misfires)
- While it streams: "…the recall trace already shows what it's about to use, so you can see the
  reasoning before the words arrive."
- If a fact doesn't recall first try: "let me ask that more directly" (rephrase); the trace still
  makes the point.
- If you fumble a login: "one second — this is the wall doing its job; each identity only sees its
  own." Then continue.
