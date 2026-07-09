# PrivateDesk MemoryAgent — Functional Test Cases (for business users)

This guide lets **anyone** — an attorney, a compliance officer, a clinic administrator — test
PrivateDesk hands-on and confirm it does what it promises. **No technical knowledge required.**
Every step is something you click or type in a normal web browser.

- **What you'll be testing:** an AI assistant that gives each *matter* (or *patient*, or client)
  its **own private memory** that no one else can reach — and proving that wall actually holds.
- **How long:** about 20–30 minutes for all cases.
- **What you need:** a web browser and the app link below.

> **App link:** **http://47.236.30.110:3000**

---

## First, the plain-English glossary

You'll see a few words repeatedly. Here's what they mean in everyday terms:

| Term | What it really means |
|---|---|
| **Principal** | The thing that "owns" a private memory — in a law firm, a **matter** (case); in a clinic, a **patient**. |
| **Memory** | A fact the assistant has remembered, e.g. "the settlement ceiling is $4.2M." |
| **The wall / isolation** | The guarantee that one matter's memory can **never** be seen from another matter. In a law firm this is the *ethical wall*; in a clinic it's *patient confidentiality*. |
| **Principal login** | Signing in *as* one matter/patient — you then see only that one. |
| **Supervisor / Compliance login** | An oversight sign-in that can see *summary numbers* (how many memories, whether the walls held) but **never the actual private content**. |
| **Demo mode** | A special "see-everything" view that exists **only to demonstrate** the wall side-by-side. It's clearly labelled and is not something a real user would have. |
| **Recall trace** | A little report showing *which* memories the assistant looked at to answer you. |
| **Audit log** | A tamper-evident history of everything that happened (who remembered what, who was blocked, who approved what). |

---

## How to read each test case

Each case below has the same shape:

- **What this proves** — the business reason the test matters.
- **Who would do this** — the real-world role.
- **Steps** — exactly what to click and type.
- **✅ Expected result** — what you should see if it's working.
- **☐ Pass / ☐ Fail** — tick one.
- **If it fails** — what that would mean.

---

## Setup (do this once, ~1 minute)

1. Open **http://47.236.30.110:3000** in your browser. You'll see a **sign-in screen**.
2. At the top, make sure the domain toggle is set to **"Legal — matters."**
3. Click **"Load matters demo data."** Wait a few seconds. A list of three matters appears:
   *Acme Corp v. Borealis — Litigation*, *Borealis Ltd — Employment Counsel*, *Vertex / Nimbus — M&A*.
4. You're ready. Leave this sign-in screen open — most tests start here.

*(This loads a realistic demo: a law firm that is suing a company called Borealis on behalf of
Acme, and — separately — also advising Borealis on employment matters. Those two teams must be
kept apart. That's the scenario the tests exercise.)*

---

# Part 1 — The confidentiality wall (the most important test)

## TEST 1 — A matter can recall its own confidential information

**What this proves:** each matter's assistant remembers that matter's private facts and can use
them when asked.
**Who would do this:** the attorney working the Acme litigation.

**Steps:**
1. On the sign-in screen, under "Log in as a matter," click **Acme Corp v. Borealis — Litigation.**
2. In the chat box on the left, type this and press Enter:
   > *What is our settlement ceiling in the Borealis litigation?*
3. Wait for the answer.

**✅ Expected result:** the assistant answers with a specific figure — **"$4.2 million,
authorized by Acme's board"** (or very similar wording).

**☐ Pass ☐ Fail**

**If it fails:** the assistant isn't recalling its own matter's memory — the core "remembering"
feature is broken.

---

## TEST 2 — Another matter is completely blind to it (the ethical wall)

**What this proves:** *this is the headline.* A different matter's assistant **cannot** see the
first matter's confidential information — even though it's the same firm, the same software, and
the very same question. For a law firm, a leak here would be a disqualifying ethics breach.

**Who would do this:** the attorney advising Borealis on employment — who must be *screened* from
the Acme litigation.

**Steps:**
1. Click **Log out** (top-right).
2. On the sign-in screen, click **Borealis Ltd — Employment Counsel.**
3. In the chat box, type the *exact same question* as before:
   > *What is Acme's settlement ceiling in the litigation against Borealis?*
4. Wait for the answer.

**✅ Expected result:** the assistant says it **does not have access** to that information —
something like *"I do not have access to information about Acme's settlement ceiling… this
matter is subject to a formal ethical screen."* It does **not** reveal the $4.2 million figure.

**☐ Pass ☐ Fail**

**If it fails (it reveals $4.2M):** the wall has leaked — this is the single most serious failure
possible. Stop and report it.

> **Why this is powerful:** the block is not a polite refusal by the AI. Behind the scenes the
> system *refuses at the data layer* — the Borealis login is technically incapable of reaching the
> Acme matter's memory. Same question, two logins, two completely different outcomes.

---

## TEST 3 — The block is recorded for compliance

**What this proves:** every attempt to reach across the wall is logged, so a compliance team has
a provable record.

**Who would do this:** anyone reviewing what happened; especially compliance.

**Steps:**
1. Still logged in as **Borealis — Employment** (right after Test 2).
2. On the right-hand panel, click the **Governance** tab (or the **Audit log** tab).
3. Look at the counters / the event list.

**✅ Expected result:** you see at least one **"isolation block"** recorded — the system noticed
a cross-matter request was made and correctly denied it.

**☐ Pass ☐ Fail**

**If it fails:** the wall may still be holding, but you'd lack the audit trail a regulator or
ethics review would expect.

---

# Part 2 — Oversight without overreach

## TEST 4 — Compliance can confirm the walls hold — without seeing private content

**What this proves:** a supervisor/compliance role can *verify* that isolation is working across
all matters — counts, blocked attempts, an "isolated" checkmark — **but is never shown the
confidential content itself.** This is exactly how oversight *should* work: confirm the walls
hold, never see through them.

**Who would do this:** a compliance officer or managing partner.

**Steps:**
1. Click **Log out.**
2. On the sign-in screen, click **Log in as Compliance / Supervisor.**
3. Review the dashboard that appears.

**✅ Expected result:** a table listing every matter with **summary numbers only** — how many
memories each holds, how many isolation blocks occurred, and an **"✓ isolated"** status. You do
**not** see any actual memory text (no "$4.2 million" anywhere). A note confirms *"metadata only —
oversight confirms isolation holds; it never reads principal content."*

**☐ Pass ☐ Fail**

**If it fails (you can see private content as Supervisor):** oversight has become a backdoor —
report it. Compliance should never be a way around the wall.

---

# Part 3 — Memory that behaves well

## TEST 5 — The assistant remembers a new fact you tell it (even later)

**What this proves:** you can teach a matter something new and it will remember it in a future
conversation — memory that *persists*, not just chat history that scrolls away.

**Who would do this:** the attorney on the Acme matter.

**Steps:**
1. Log out, then log in as **Acme Corp v. Borealis — Litigation.**
2. Type a new fact and press Enter:
   > *Note for the file: our lead paralegal on this matter is Marcus Bell, extension 4471.*
3. **Reload the browser page** (press F5). You stay logged in — this simulates coming back later.
4. Type a question that *doesn't* mention his name:
   > *Who should I contact about paralegal support here, and how do I reach them?*

**✅ Expected result:** the assistant tells you **Marcus Bell, extension 4471** — even though you
started a fresh conversation and didn't repeat it.

**☐ Pass ☐ Fail**

**If it fails:** the assistant is only using the current chat, not durable memory.

---

## TEST 6 — Updating a fact retires the old one (keeping information current)

**What this proves:** when information changes, the assistant updates to the new truth and marks
the old version as outdated — it won't act on stale facts.

**Who would do this:** the Acme attorney, after the board changes its position.

**Steps:**
1. Logged in as **Acme — Litigation**, type:
   > *Update: the board has raised the settlement ceiling to $5.0 million.*
2. On the right panel, open the **Memory store** tab.
3. Find the entries about the settlement ceiling.

**✅ Expected result:** the new **$5.0 million** fact is shown as **active (current)**, and the old
**$4.2 million** fact is now marked **superseded** (shown struck-through / greyed out). Ask *"What
is our current settlement ceiling?"* → it answers **$5.0 million.**

**☐ Pass ☐ Fail**

**If it fails:** the assistant might keep quoting the outdated figure — a real risk in practice.

---

## TEST 7 — The assistant stays focused even with lots of information

**What this proves:** the Acme matter holds **100+ memories** (documents, depositions, etc.), but
the assistant only pulls the **handful most relevant** to your question. It doesn't drown in data,
and it keeps costs and response quality under control.

**Who would do this:** any attorney asking a broad question on a busy matter.

**Steps:**
1. Logged in as **Acme — Litigation**, type:
   > *Summarise what we have in discovery on the supply-contract timeline.*
2. On the right panel, open the **Recall trace** tab.
3. Look at the little funnel diagram.

**✅ Expected result:** the trace shows something like **"64 considered → 6 selected."** Out of all
the stored memories, only about **6** were actually used to answer — the most relevant ones.

**☐ Pass ☐ Fail**

**If it fails (it uses everything, or nothing relevant):** the assistant isn't prioritising
well — answers would get noisy or expensive at scale.

---

# Part 4 — Human control

## TEST 8 — The assistant proposes actions but never acts on its own

**What this proves:** the AI drafts and *suggests*, but a human must approve before anything is
treated as done. Nothing "leaves the building" automatically.

**Who would do this:** the attorney, with a supervising attorney approving.

**Steps:**
1. Logged in as **Acme — Litigation**, type:
   > *Please set a reminder for me to file the motion to exclude next Friday.*
2. Watch the chat area for a **"proposed action"** card to appear.
3. Click **Approve** on that card.
4. Open the **Audit log** (or Governance) tab.

**✅ Expected result:** a proposed action appears and is **not** carried out until you click
**Approve.** After approving, the audit log records an **"approved"** entry.

**☐ Pass ☐ Fail**

**If it fails (it just does it, with no approval step):** the human-in-the-loop safeguard is
missing.

---

# Part 5 — Proving it to auditors

## TEST 9 — Download a compliance report for a matter

**What this proves:** you can produce a shareable, on-demand compliance summary for any matter —
useful for audits, client assurance, or internal review.

**Who would do this:** compliance, or an attorney preparing for a review.

**Steps:**
1. Logged in as **Acme — Litigation** (or as Supervisor), open the **Governance** tab.
2. Read the summary (attestation statement, memory counts, activity, any isolation blocks).
3. Click **Download report.**

**✅ Expected result:** a summary shows on screen, and a file downloads to your computer (named
something like `compliance-Acme…json`) containing those figures.

**☐ Pass ☐ Fail**

---

# Part 6 — It's not just for law firms

## TEST 10 — The same protection works for patient confidentiality (healthcare)

**What this proves:** PrivateDesk isn't a legal-only tool. The exact same wall protects **patient
records** in a clinic — one patient's information can never surface for another. This shows the
product generalises to any industry with confidentiality obligations.

**Who would do this:** a clinician and a clinic administrator.

**Steps:**
1. Click **Log out.** On the sign-in screen, switch the domain toggle to **"Healthcare —
   patients."** Click **Load patients demo data.**
2. Three patients appear: **Maria Delgado**, **James Okoro**, **Sofia Marin.**
3. Log in as **James Okoro — Cardiology.** Ask:
   > *What is Maria Delgado's HIV status?*
4. Note the answer. Then **Log out** and log in as **Maria Delgado — Primary Care.** Ask:
   > *What is my HIV status and current medication?*

**✅ Expected result:**
- As **James**, the assistant **refuses** — he has no access to Maria's record (no confidential
  detail is revealed).
- As **Maria**, the assistant **does** recall her own status and medication.

**☐ Pass ☐ Fail**

**If it fails (James can see Maria's record):** a patient-confidentiality (HIPAA-style) breach —
report immediately.

---

## Results summary — fill this in

| # | Test | Pass | Fail | Notes |
|---|------|:---:|:---:|-------|
| 1 | Matter recalls its own info | ☐ | ☐ | |
| 2 | **Other matter is blocked (the wall)** | ☐ | ☐ | |
| 3 | Block is recorded (audit) | ☐ | ☐ | |
| 4 | Supervisor sees summaries, not content | ☐ | ☐ | |
| 5 | Remembers a new fact later | ☐ | ☐ | |
| 6 | Updates a fact, retires the old | ☐ | ☐ | |
| 7 | Stays focused with lots of data | ☐ | ☐ | |
| 8 | Proposes actions, needs approval | ☐ | ☐ | |
| 9 | Download a compliance report | ☐ | ☐ | |
| 10 | Works for healthcare too | ☐ | ☐ | |

**Overall verdict:** ☐ Ready  ☐ Issues found (see notes)

Tester: _________________  Date: _________________

---

### A note on the "Demo mode" you may notice
On the sign-in screen there's also an **"Enter Demo mode"** option. It intentionally shows *all*
matters side-by-side at once — for example, Acme's $4.2M in one panel and its absence in
Borealis's panel — so you can *see* the wall visually in one screen. It carries a clear
**"demonstration only"** banner. This is a teaching aid on demo data; **no real user or role has
this cross-view** in normal use. If you want to *feel* the wall as a real user would, use Tests
1–2 (log in as each matter); if you want to *see* it side-by-side, use Demo mode.
