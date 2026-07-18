# PrivateDesk — Demo Video Script (≈3:15)

**Target:** ~3:00–3:15 · Qwen Cloud Global AI Hackathon, Track 1 (MemoryAgent)
**Structure:** **Part 1 (~1 min)** explains what PrivateDesk is (problem → the one idea →
architecture); **Part 2 (~2 min)** demos the use case — the four scored behaviors (accumulation ·
isolation · forgetting · bounded recall) + human-in-the-loop, plus metadata-only oversight and the
**second domain (healthcare)** that proves this is a memory *substrate*, not a legal app.
**The money shot is isolation** (1:18–1:52) — give it room; everything else is brisk.

> **Editing note — this is what keeps it tight:** cut the dead air while the LLM streams. Record
> naturally, then trim every wait. The recall **trace appears before the tokens**, so you can keep
> talking over it. To hit a hard 3:00, drop the Oversight beat (1:52–2:04) and trim the intro to ~45s.

---

**Prefer to talk naturally, no clock?** See [`demo-script-natural.md`](demo-script-natural.md).

## Pre-flight (before you hit record)

- [ ] **Start the box** (it's kept stopped to avoid charges): `make infra-start` → same IP, ~1–2 min.
      Run `make infra-stop` when you're done.
- [ ] `curl http://47.236.30.110:8000/health` → `"provider":"Qwen Cloud (DashScope)"`, `"llm_ok":true`.
- [ ] Open http://47.236.30.110:3000 (keep the URL visible so judges see it's really deployed).
- [ ] On the **login screen**: domain **Legal — matters** → **Load matters demo data** (3 matters,
      110+ discovery memories on the litigation matter).
- [ ] Have a second browser tab with **`docs/architecture.png`** open for the 0:10 flash.
- [ ] Optional but strong: run `make smoke` (12/12) and `make evals` (100/100) so you can quote them.
- [ ] Browser full-screen, one tab, bookmarks hidden, zoom ~110%.
- [ ] Record the **proof-of-deployment** clip separately — [`VIDEO-SCRIPT-ALIBABA-PROOF.md`](VIDEO-SCRIPT-ALIBABA-PROOF.md).

---

## The script

Two parts: **~1 min explaining PrivateDesk**, then **~2 min demoing the use case**. Total ≈ 3:15.
(To trim to 3:00, drop the Oversight beat and tighten the intro to ~45s — see the trim note.)

---

## Part 1 — What PrivateDesk is  (0:00–1:00)

*Narration-led. On screen: start on the login screen, move to the **architecture diagram** for the
middle, end back on the cockpit. Speak calmly — this is the "why".*

### 0:00–0:22 — The problem
| | |
|---|---|
| **On screen** | Login screen (or a simple title card). Cursor still. |
| **Say** | "Every AI agent needs memory. But most 'AI memory' today is one big shared database with a customer label bolted on — and one missing filter leaks one client's data into another's answer. In a law firm, or a hospital, that isn't a bug — it's a confidentiality breach. **PrivateDesk** fixes that at the root." |

### 0:22–0:44 — What it is + the one idea
| | |
|---|---|
| **On screen** | Switch to the **architecture diagram** (`docs/architecture.png`). Trace: frontend → backend → the chokepoint → Qdrant/Postgres. |
| **Say** | "PrivateDesk is a **private memory layer for AI agents**. Every *principal* — a legal matter, a patient, a tenant — gets its own persistent memory that no one else can reach. And the isolation is **structural, not hopeful**: every memory read goes through a *single chokepoint* that's always scoped to one principal, and a guard test fails the build the moment anything crosses. The wall is **provable, not promised**." |

### 0:44–1:00 — The engine, the stack, and where it runs
| | |
|---|---|
| **On screen** | Diagram → pan the empty cockpit. Show the login roles (principal / supervisor / demo). |
| **Say** | "On top of that isolation sits a real memory engine — it remembers across sessions, retires outdated facts, and recalls only the few most relevant memories under a token budget — and a human approves any action. It's a Next.js cockpit over a FastAPI engine, Postgres and Qdrant, powered by **Qwen** — and the *same code* runs fully local on open weights. It's live on Alibaba Cloud. Let me show you, inside a law firm." |

---

## Part 2 — The use case  (1:00–3:15)

> **When do I log out?** You **stay logged in as Acme** for the first three beats (Accumulation →
> Bounded recall → Forgetting — all the same matter). You only **log out to switch identity**: for
> Isolation (→ Borealis, then Demo mode), Oversight (→ Supervisor), and Healthcare (→ James).
> The **recall trace is not a login thing** — it appears automatically whenever you send a chat
> message, and the app switches to the Recall-trace tab for you.

### 1:00–1:18 — Accumulation
| | |
|---|---|
| **On screen** | **Log in as → Acme — Litigation.** ① Type a **new** fact: *"Note for the file: our lead paralegal is Marcus Bell, extension 4471."* Send, let the reply finish. ② Click the **Memory store** tab — the Marcus Bell memory is now a saved row (this confirms it persisted). ③ **Reload the page** (F5 — you stay logged in; this is a fresh session, **no logout**). ④ Ask: *"Who's our paralegal here and how do I reach them?"* → answers **Marcus Bell, ext 4471**, and the **Recall trace** tab opens on its own. |
| **Say** | "I tell Acme a brand-new fact — our paralegal, Marcus Bell. It's now a stored memory, right here. I reload into a completely fresh session… and it still knows, down to the extension. The recall trace shows it pulled that exact memory back — persistent memory, not chat history." |

### 1:18–1:52 — Isolation: the ethical wall ← **the money shot**
| | |
|---|---|
| **On screen** | **Log out → Log in as → Borealis — Employment.** Ask: *"What's Acme's settlement position against Borealis?"* → no access. *(Optional: devtools Network → the request returns **403**.)* Then **Log out → Enter Demo mode** → **Ethical wall** tab (note the *"demonstration only"* banner): **$4.2M** in the Acme pane, **absent** in Borealis's. Open **Governance/Audit** → the **`isolation_block`** event. |
| **Say** | "Here's the test. The firm sues Borealis for Acme — and *separately* advises Borealis; those teams must be screened. So I log in as the *Borealis* attorney and ask for Acme's settlement strategy… no access. And this isn't the model being polite — the **API itself returns 403**; one principal's login physically cannot reach another's memory. Side by side: Acme's privileged $4.2 million ceiling lives here, and simply doesn't exist in Borealis's world — and the attempt is logged as an isolation block." |

### 1:52–2:04 — Oversight without overreach
| | |
|---|---|
| **On screen** | **Log out → Log in as Compliance / Supervisor.** Metadata dashboard: per-matter counts, isolation blocks, "✓ isolated". Scroll — **no memory content**. |
| **Say** | "Compliance still needs assurance — so an oversight login sees *that* the walls hold: counts, blocked attempts, attestation — and never sees *through* them. Oversight isn't a backdoor." |

### 2:04–2:20 — Bounded recall at scale
| | |
|---|---|
| **On screen** | Back in **Acme — Litigation** (115 memories). Ask: *"What discovery do we have on the supply-contract timeline?"* → **Recall trace**: funnel **64 retrieved → a few (deduplicated) into context**, with the token count. |
| **Say** | "This matter holds over a hundred discovery memories. Watch the funnel — 64 retrieved, ranked by similarity, importance and recency, and only the few most relevant (deduplicated) entered the context, under a token budget. The store grows forever; the prompt stays small." |

### 2:20–2:35 — Forgetting
| | |
|---|---|
| **On screen** | Type: *"Update: the board raised the settlement ceiling to $5M."* Open **Memory store** — old **$4.2M** now **superseded** (struck through), **$5M** active. |
| **Say** | "Memory has to stay current. I raise the ceiling — and the old figure is automatically retired as superseded, not silently kept. The assistant acts on the new truth." |

### 2:35–2:52 — Same engine, different industry (healthcare)
| | |
|---|---|
| **On screen** | **Log out** → toggle domain to **Healthcare — patients** → **Load patients demo data**. **Log in as James Okoro — Cardiology.** Ask: *"What is Maria Delgado's HIV status?"* → refused. |
| **Say** | "And this isn't a legal app. Flip the domain — now the principals are **patients**. On James's chart I ask for another patient's HIV status — refused. Identical engine, identical chokepoint; the ethical wall just became **patient confidentiality**. Changing industry is *data, not code*." |

### 2:52–3:04 — Human-in-the-loop
| | |
|---|---|
| **On screen** | Ask: *"Please set a reminder to file the motion to exclude next Friday."* A **proposed action** card appears → click **Approve** → audit shows `hitl_approved`. |
| **Say** | "And nothing acts on its own — the assistant *drafts*, a human approves, and the decision is audited." |

### 3:04–3:16 — Close (the proof)
| | |
|---|---|
| **On screen** | Terminal: `make evals` → **100/100**, and `pytest tests/test_isolation.py` → **1 passed**. Land on the cockpit. |
| **Say** | "The wall isn't a prompt — it's enforced in the retrieval layer, extended even to the LLM's prompt cache, and it's **measured**: every behavior scores 100 out of 100, and a guard test fails the build if a single memory ever crosses. Private memory your auditor can verify — on Qwen Cloud, or fully local on open weights. Built on Qwen." |

---

## Tips
- **Trim the waits.** Each beat is 15–25s of *content*; record loose, cut tight.
- Keep the cursor deliberate — judges follow your pointer. Hover the thing you're naming.
- Each beat is self-contained: fluff a line, pause, redo just that beat.
- The most important 15 seconds is **the 403 + the side-by-side wall**. If you nail one thing, nail that.
- Don't rush the close — "isolation, open weights, never training" is the thesis.

## If you'd rather go long (~4:30)
"About 3 minutes" is the rule, so the above is the safe cut. If you decide a longer version is
acceptable, the natural expansions are: show the **compliance report download** (+15s), the
**local/open-weight** path in `/health` (+20s), the **cache-partition** explanation (+25s), and the
**maintenance sweep** for forgetting (+15s). Keep the 3:00 cut as the submitted video.
