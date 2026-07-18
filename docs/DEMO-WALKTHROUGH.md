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

Loading a domain from the **login screen** (or a fresh deploy) creates one firm and three matters. Each matter
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

Open **http://47.236.30.110:3000** — you land on a **login screen**.

### Sign in (this is the entry point now)
```
┌──────────────────────────────┐
│ PD  PrivateDesk MemoryAgent   │
│ Demo domain: [Legal][Health]  │  ← pick a domain, then "Load … demo data"
│ Log in as a matter:           │
│   • Acme — Litigation         │  ← per-principal login (scoped to that one)
│   • Borealis — Employment     │
│   • Vertex / Nimbus — M&A     │
│ ───────────────────────────   │
│ • Compliance / Supervisor     │  ← metadata-only oversight
│ • Enter Demo mode             │  ← god-view for the isolation demonstration
└──────────────────────────────┘
```
Three ways in, each meaningful:
- **Log in as a principal** → the cockpit is **locked to that matter/patient** (the API returns 403 for anything else). No switching.
- **Compliance / Supervisor** → a cross-principal **metadata dashboard** (counts, isolation-blocks, attestation) — **never content**.
- **Demo mode** → the full god-view (all principals + the side-by-side Ethical Wall), with a **"demonstration only"** banner.

Once inside (principal or demo), the cockpit is:
```
┌───────────────────────────────┬───────────────────────────────────────────┐
│         CHAT                  │ [Memory][Recall trace][Audit][Wall*][Gov]  │
│  (messages + Approve/Reject)  │            INSPECTOR                       │
└───────────────────────────────┴───────────────────────────────────────────┘
   * "Ethical wall" tab appears in Demo mode only
```
Inspector tabs: **Memory store** (+ Run maintenance), **Recall trace**, **Audit log**,
**Ethical wall** (demo only — side-by-side), **Governance** (attestation + downloadable report).

---

## 3. The walkthrough (in demo order)

### ▶ Behavior 2 — Isolation (lead with this)

The login flow makes this the strongest beat: **the same question, two identities.**

**Step 1 — log in as the matter that owns the fact.**
On the login screen (Legal domain), click **Log in as → Acme — Litigation**. Ask:

> What is our settlement ceiling in the Borealis litigation?

Expected answer (verified):
> *"Our settlement ceiling in the Borealis litigation is **$4.2 million** — authorized by Acme's board."*

Open the **Recall trace** tab (it auto-switches on send): the `$4.2M` fact is the top
selected memory (`similarity ≈ 0.80`, `salience 0.97`).

**Step 2 — a different identity is blind to it.**
Click **Log out**, then **Log in as → Borealis — Employment Counsel**. Ask the *same thing*:

> What is Acme's settlement ceiling in the litigation against Borealis?

Expected answer (verified):
> *"I do not have access to information about Acme's settlement ceiling — or any details
> related to the Acme litigation — because this matter is subject to a formal ethical screen…"*

> This isn't a UI filter — the API itself returns **403** if this identity requests the
> litigation matter's data. The wall is enforced server-side, per logged-in principal.

**Step 3 — show the receipts.**
- Open **Audit log** (or the **Governance** tab) → an **`isolation_block`** event is recorded.
- **For the side-by-side visual:** log out and **Enter Demo mode** → the **Ethical wall** tab
  renders both matters — $4.2M present in one, absent in the other — under the explicit
  *"demonstration only"* banner.
- **For the oversight story:** log in as **Compliance / Supervisor** → the dashboard shows both
  matters' counts + isolation-blocks + attestation, and **no memory content** at all.

> **Talking point:** "Same question, two logins. The litigation attorney gets $4.2M. The
> Borealis employment attorney gets a 403 — not a redaction, an enforced wall. And compliance
> can confirm the wall holds without ever seeing through it."

### ▶ Behavior 1 — Accumulation

Log in as (or stay on) the **Litigation** matter.

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
  candidates retrieved (64)  →  de-duplicated, selected into context (a few)   ≈ tokens: ~100
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

## 5. Switch domains, reset & re-run

- **Domain switch** — on the **login screen**, toggle **Legal — matters** ⇄ **Healthcare —
  patients** and click **Load … demo data**. Healthcare gives you 3 patients (Maria / James /
  Sofia); the confidentiality wall is identical — as **James**, ask for **Maria's HIV status**
  → blocked; as **Maria**, it returns.
- **Reset** — clicking **Load / Reseed** wipes and reloads that domain. The seed is
  **self-healing** (verifies every memory has a live vector; reports `vectors_healed`).
- **Idempotent** — reseeding, restarting, or redeploying all converge to the same clean state.

---

## 6. Suggested 3-minute narrative

The full shot-by-shot version (with the exact lines to say) is
[`demo-video-script.md`](demo-video-script.md). In brief:

1. **(0:00) Frame it + architecture.** Login screen; flash the architecture diagram. "Every matter
   gets its own assistant behind a login; every memory read goes through one isolation chokepoint;
   models from Qwen Cloud — or fully local on open weights."
2. **(0:18) Accumulation.** Tell Litigation a fact → reload → it still knows; show the recall trace.
3. **(0:42) Isolation ← the money shot.** Log out → log in as **Employment** → same question →
   **403 / no access**. Then **Demo mode** → side-by-side wall ($4.2M here / absent there, under the
   "demonstration only" banner) + the `isolation_block` event.
4. **(1:22) Oversight.** Log in as **Supervisor** → metadata dashboard: the walls hold, and it sees
   **no content**. "Oversight isn't a backdoor."
5. **(1:40) Bounded recall.** Broad discovery question → funnel **64 → a few** (de-duplicated) out of 115 stored.
6. **(2:00) Forgetting.** Raise the ceiling to $5M → the $4.2M memory flips to **superseded**.
7. **(2:18) Healthcare — same engine.** Switch domain → log in as **James** → ask for **Maria's HIV
   status** → refused. "The ethical wall just became patient confidentiality. Data, not code."
8. **(2:38) Human-in-the-loop.** Ask for a reminder → **Approve** → audited.
9. **(2:52) Close.** `make evals` **100/100** + isolation guard `1 passed`. "The wall isn't a
   prompt — it's enforced, extended to the LLM cache, and measured."

---

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| App/health won't load | Confirm the ECS security group allows inbound **3000** and **8000**; check `curl http://<ip>:8000/health`. |
| `"llm_ok": false` on `/health` | The DashScope key is missing/invalid in the server `.env`; re-check `TF_VAR_dashscope_api_key` and redeploy. |
| A matter "has no access" to its **own** facts | Vectors didn't land for that matter. **Reseed** from the login screen — the self-heal re-embeds any missing vectors. (Root cause fixed: durable upserts + post-seed verification.) |
| Login returns to the login screen immediately | Token expired/cleared or `SESSION_SECRET` changed on redeploy — just log in again. |
| "Can't reach the API" banner in the UI | `NEXT_PUBLIC_API_BASE` must be the reachable API URL baked at build time (`http://<public-ip>:8000`). The IaC handles this automatically. |
| Chat returns nothing | Check `docker compose logs api` on the box for an LLM/embedding error (rate limit, key). |

---

*See [`TECHNICAL-ARCHITECTURE.md`](TECHNICAL-ARCHITECTURE.md) for how each component works under
the hood.*
