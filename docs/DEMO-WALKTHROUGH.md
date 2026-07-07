# PrivateDesk MemoryAgent — Demo Walkthrough

A complete, click-by-click script for demonstrating the system, plus the exact prompts
to type and the responses to expect. Everything below was verified against the live
deployment.

- **Live app:** http://47.236.30.110:3000
- **Live API health:** http://47.236.30.110:8000/health → expect `"llm_ok": true`
- **Scenario:** a law firm ("Demo Law Firm LLP") running three legal matters, where the
  memory wall between matters is the **ethical wall**.

---

## 0. What the demo proves

Track 1 (MemoryAgent) scores four behaviors. This demo shows all four **plus** a
human-in-the-loop gate:

| # | Behavior | One-line proof |
|---|----------|----------------|
| 1 | **Accumulation** | A fact told to a matter is recalled later, unprompted, in a new session. |
| 2 | **Isolation** | One matter's assistant cannot read another matter's memory — the ethical wall. |
| 3 | **Forgetting** | Superseded facts are deprecated; expired/low-salience ones are swept. |
| 4 | **Bounded recall** | With 115 memories on one matter, only the top ~6 relevant ones enter the prompt. |
| ✚ | **Human-in-the-loop** | The assistant *drafts* actions; an attorney approves before anything is "done." |

The single most important moment is **#2 Isolation** — same question, two matters, only
the owning matter can answer.

---

## 1. The seeded world

Clicking **Seed demo** (or a fresh deploy) creates one firm and three matters. Each matter
is a **separate principal with its own isolated memory namespace**:

| Matter (principal) | Persona | Seeded memory |
|---|---|---|
| **Acme Corp v. Borealis — Litigation** | Litigation assistant | 5 privileged facts **+ 110 bulk discovery items** (115 total) |
| **Borealis Ltd — Employment Counsel** | Employment assistant | 4 employment facts |
| **Vertex / Nimbus — M&A** | Corporate/M&A assistant | 4 deal facts |

The first two matters are a deliberate **ethical-wall pair**: the firm *sues* Borealis (for
Acme) **and separately advises** Borealis on employment — so the two teams must be screened
from each other.

The five privileged litigation facts (these are the "needles"):

1. *Acme's board authorized a settlement ceiling of **$4.2M** in the Borealis litigation.* (salience 0.97)
2. *Litigation strategy: move to exclude the Borealis email chain as hearsay before trial.* (0.92)
3. *Dr. Lena Ortiz is Acme's lead expert witness; her deposition is set for next month.* (0.88)
4. *Trial is scheduled to begin the first Monday of next quarter.* (0.75)
5. *Borealis is the opposing party (the firm also advises Borealis on a separate, screened matter).* (0.70)

The other 110 litigation memories are realistic filler — Bates-stamped documents, deposition
calendar entries, interrogatory responses — there to create a **needle-in-a-haystack** recall
challenge (behavior #4).

---

## 2. Orientation — the cockpit UI

Open **http://47.236.30.110:3000**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PD  PrivateDesk MemoryAgent      [Litigation] [Employment] [M&A]  [Seed] │  ← principal picker
├───────────────────────────────┬───────────────────────────────────────────┤
│                               │  [Memory store][Recall trace][Audit][Wall]│  ← inspector tabs
│         CHAT                  │                                           │
│   (messages + proposed        │            INSPECTOR                      │
│    action Approve/Reject)     │     (whatever tab is selected)            │
│                               │                                           │
└───────────────────────────────┴───────────────────────────────────────────┘
```

- **Top bar** — three matter "pills" (the principals) and a **Seed demo** button.
- **Left** — the Chat panel. Proposed actions appear here with **Approve / Reject**.
- **Right** — the Inspector with four tabs:
  - **Memory store** — every memory for the selected matter (kind, status, salience) + a **Run maintenance** button.
  - **Recall trace** — the retrieval funnel for the last message (candidates → selected, ≈ tokens).
  - **Audit log** — every `memory_write`, `memory_recall`, `isolation_block`, `memory_maintenance`, `hitl_*` event.
  - **Ethical wall** — two matters side by side, showing their stores are physically separate.

> **Always click a matter pill first.** Selecting a principal starts a session and loads
> its inspector.

---

## 3. The walkthrough (in demo order)

### ▶ Behavior 2 — Isolation (lead with this)

**Step 1 — the owning matter answers.**
Click **Acme Corp v. Borealis — Litigation**. Type:

> What is our settlement ceiling in the Borealis litigation?

Expected answer (verified):
> *"Our settlement ceiling in the Borealis litigation is **$4.2 million** — authorized by Acme's board."*

Open the **Recall trace** tab (it auto-switches on send): the `$4.2M` fact is the top
selected memory (`similarity ≈ 0.80`, `salience 0.97`).

**Step 2 — a different matter is blind to it.**
Now click **Borealis Ltd — Employment Counsel**. Ask the *same thing*:

> What is Acme's settlement ceiling in the litigation against Borealis?

Expected answer (verified):
> *"I do not have access to information about Acme's settlement ceiling — or any details
> related to the Acme litigation — because this matter is subject to a formal ethical screen…"*

**Step 3 — show the receipts.**
- Open **Audit log** → an **`isolation_block`** event is recorded (rose-colored).
- Open **Ethical wall** → the two matters render side by side; each shows only its own
  active memories. There is no code path that lets one read the other.

> **Talking point:** "Same question. The litigation team gets $4.2M. The Borealis employment
> team gets nothing — not a redaction, an actual wall. The store is physically separate."

### ▶ Behavior 1 — Accumulation

Stay on the **Litigation** matter.

**Step 1 — state a new fact:**
> New fact: our lead paralegal on this matter is Marcus Bell, ext. 4471.

Open **Memory store** → a new entry appears; **Audit log** shows a `memory_write`.

**Step 2 — recall it indirectly, as if a new session:**
> Who should I contact about paralegal support here, and how?

Expected: the assistant surfaces **Marcus Bell / ext. 4471** without you re-stating it.
The **Recall trace** shows the new memory was retrieved.

> **Persistence proof:** reload the browser tab. The Memory store still lists Marcus Bell —
> memories are durable in Postgres + Qdrant, not just chat scrollback.

### ▶ Behavior 4 — Bounded recall (115 memories → ~6)

On the **Litigation** matter (115 memories), ask something broad:

> Summarize what we have in discovery so far.

Open **Recall trace** and read the funnel:

```
  candidates retrieved (64)  →  selected into context (6)   ≈ tokens: ~100
```

Out of **115 stored** memories, **64** are pulled as vector candidates, then the reranker
keeps only the **top 6** for the prompt (bounded by `K_CONTEXT=6`). Each selected row shows
`sim / sal / score`. This is the "100+ memories, only the few relevant ones enter the prompt,
under a token budget" behavior.

> **Talking point:** "Memory doesn't mean stuffing everything into the context window. It
> means retrieving a lot, ranking by similarity + importance + recency, and injecting only a
> handful."

### ▶ Behavior 3 — Forgetting

On the **Litigation** matter:

**Step 1 — supersede a fact:**
> Update: the board raised the settlement ceiling to $5.0M.

Open **Memory store**: the old *$4.2M* entry flips to **`superseded`** (rose badge,
struck-through); the new *$5.0M* fact is `active`. (The engine detects the update via a
similarity + LLM "does this supersede?" check.)

**Step 2 — sweep:**
Click **Run maintenance** (top-right of the Memory store tab). A line appears:

> *"Swept: N expired, M pruned."*

This expires anything past its `expires_at` and prunes low-salience memories unused for >30
days. **Audit log** records a `memory_maintenance` event. Watch the "active / total" counter
drop.

### ▶ Human-in-the-loop

On any matter, ask for an action:

> Remind me to file the motion to exclude the Borealis email chain next Friday.

*(or: "Draft a message to opposing counsel proposing a deposition date.")*

A **Proposed action** card appears in the **Chat panel** with **Approve / Reject** — it is
**not** auto-executed. Click **Approve** → **Audit log** records `hitl_approved` (or
`hitl_rejected`). This is the attorney gate: assistants draft, a human commits.

---

## 4. Prove the wall at the infrastructure level (optional, high-impact)

Beyond the UI, the isolation property has an automated guard test. From the `infra/terraform`
directory on the deploy machine:

```bash
eval "$(terraform output -raw isolation_test_command)"
# → runs tests/test_isolation.py on the server: 1 passed
```

Or directly:

```bash
ssh -i infra/terraform/generated/privatedesk.pem root@47.236.30.110 \
  'cd privatedesk-memoryagent && docker compose exec -T api pytest -q tests/test_isolation.py'
# 1 passed  ← zero cross-namespace leakage
```

> This test asserts that a search in one namespace can **never** return another namespace's
> vectors. It is the codified version of the ethical wall and stays green in CI.

---

## 5. Reset & re-run

- **Seed demo** button (top bar) — wipes and reloads the firm + three matters + 115 discovery
  memories. Safe to click repeatedly; the seed is **self-healing** (it verifies every memory
  has a live vector before returning, reporting `vectors_healed`).
- The demo is **idempotent** — reseeding, restarting, or redeploying all converge to the same
  clean state.

---

## 6. Suggested 3-minute narrative

1. **(0:00) Frame it.** "Every legal matter gets its own private assistant. The wall between
   matters is the ethical wall — and we can prove it."
2. **(0:20) Isolation.** Litigation answers $4.2M; Borealis is blind to it; show the
   `isolation_block` audit event and the Ethical Wall tab.
3. **(1:10) Accumulation.** Add the paralegal fact, recall it indirectly, reload to show
   persistence.
4. **(1:50) Bounded recall.** Broad discovery question → Recall trace funnel: 115 → 64 → 6.
5. **(2:20) Forgetting.** Supersede the ceiling → old one struck through; Run maintenance.
6. **(2:40) Human-in-the-loop.** Ask for a reminder → Approve. "Assistants draft; attorneys
   decide."
7. **(2:55) Close.** Run the isolation pytest live: `1 passed`. "The wall isn't a prompt. It's
   enforced in the retrieval layer and tested in CI."

---

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| App/health won't load | Confirm the ECS security group allows inbound **3000** and **8000**; check `curl http://<ip>:8000/health`. |
| `"llm_ok": false` on `/health` | The DashScope key is missing/invalid in the server `.env`; re-check `TF_VAR_dashscope_api_key` and redeploy. |
| A matter "has no access" to its **own** facts | Vectors didn't land for that matter. Click **Seed demo** — the self-heal re-embeds any missing vectors. (Root cause fixed: durable upserts + post-seed verification.) |
| "Can't reach the API" banner in the UI | `NEXT_PUBLIC_API_BASE` must be the reachable API URL baked at build time (`http://<public-ip>:8000`). The IaC handles this automatically. |
| Chat returns nothing | Check `docker compose logs api` on the box for an LLM/embedding error (rate limit, key). |

---

*See [`TECHNICAL-ARCHITECTURE.md`](TECHNICAL-ARCHITECTURE.md) for how each component works under
the hood.*
