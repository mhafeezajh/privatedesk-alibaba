# PrivateDesk — Demo Video Script (≈3:00)

**Target:** ~3:00 · Qwen Cloud Global AI Hackathon, Track 1 (MemoryAgent)
**Covers:** the four scored behaviors (accumulation · isolation · forgetting · bounded recall)
+ human-in-the-loop, **plus** the architecture, per-principal auth, metadata-only oversight, and
the **second domain (healthcare)** that proves this is a memory *substrate*, not a legal app.
**The money shot is isolation** (0:42–1:22) — give it room; everything else is brisk.

> **Editing note — this is what makes 3:00 possible:** cut the dead air while the LLM streams.
> Record naturally, then trim every wait. The recall **trace appears before the tokens**, so you
> can keep talking over it.

---

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

### 0:00–0:18 — Hook + architecture
| | |
|---|---|
| **On screen** | The **login screen** (domain toggle + "log in as"). At ~0:10 flash the **architecture diagram** tab for ~6s, then back. |
| **Say** | "This is PrivateDesk. Every legal matter gets its own AI assistant with private, walled-off memory — behind a login. Under the hood: a Next.js cockpit, a FastAPI memory engine, Postgres and Qdrant — and every single memory read goes through **one** isolation chokepoint. Models come from **Qwen Cloud**; the exact same code runs fully local on open-weight Qwen3. Because privacy isn't where the data lives — it's isolation, open weights, and never training on it." |

### 0:18–0:42 — Accumulation
| | |
|---|---|
| **On screen** | **Log in as → Acme — Litigation.** Type: *"Note for the file: our lead expert is Dr. Lena Ortiz; her deposition is next month."* Send. **Reload the page** (fresh session, still logged in). Ask: *"Who's our lead expert and when's the deposition?"* → correct answer. Click **Recall trace**. |
| **Say** | "I tell the Acme matter a fact… then start a brand-new session. It still knows — that fact was distilled into persistent memory, not chat history. The recall trace shows exactly which memory it pulled back." |

### 0:42–1:22 — Isolation: the ethical wall ← **spend time here**
| | |
|---|---|
| **On screen** | **Log out → Log in as → Borealis — Employment.** Ask: *"What's Acme's settlement position against Borealis?"* → no access. *(Optional: devtools Network → a request for the other matter returns **403**.)* Then **Log out → Enter Demo mode** → **Ethical wall** tab (point at the *"demonstration only"* banner): **$4.2M** in the Acme pane, **absent** in Borealis's. Open **Governance/Audit** → the **`isolation_block`** event. |
| **Say** | "Here's the test. The firm sues Borealis for Acme — and *separately* advises Borealis. Those teams must be screened. So I log in as the *Borealis* attorney and ask for Acme's settlement strategy… no access. And this isn't the model being polite — the **API itself returns 403**. A principal's login physically cannot reach another's memory. This demo view puts both stores side by side: Acme's privileged $4.2 million ceiling lives here, and simply doesn't exist in Borealis's world. The attempt is logged as an isolation block. If that leaked, the firm just handed the other side its strategy." |

### 1:22–1:40 — Oversight without overreach
| | |
|---|---|
| **On screen** | **Log out → Log in as Compliance / Supervisor.** The metadata dashboard: per-matter counts, isolation blocks, "✓ isolated". Scroll — **no memory content anywhere**. |
| **Say** | "But compliance still needs assurance. So there's an oversight login that sees *that* the walls hold — counts, blocked attempts, attestation — and **never sees through them**. No memory content, at all. Oversight isn't a backdoor." |

### 1:40–2:00 — Bounded recall at scale
| | |
|---|---|
| **On screen** | Back in **Acme — Litigation** (115 memories). Ask: *"What discovery do we have on the supply-contract timeline?"* → **Recall trace**: funnel **64 retrieved → 6 into context**, with the token count. |
| **Say** | "This matter holds over a hundred discovery memories. Watch the funnel — 64 candidates retrieved, ranked by similarity, importance and recency, and only the **six** most relevant entered the model's context, under a token budget. The store can grow forever; the prompt stays small." |

### 2:00–2:18 — Forgetting
| | |
|---|---|
| **On screen** | Type: *"Update: the board raised the settlement ceiling to $5M."* Open **Memory store** — old **$4.2M** now **superseded** (struck through), **$5M** active. Ask *"What's our current ceiling?"* → **$5M**. |
| **Say** | "Memory has to stay current. I raise the ceiling — and the old figure is automatically retired as superseded, not silently kept. The assistant now acts on the new truth, and the old one is greyed out for the record." |

### 2:18–2:38 — Same engine, different industry (healthcare)
| | |
|---|---|
| **On screen** | **Log out** → toggle domain to **Healthcare — patients** → **Load patients demo data** → three patients appear. **Log in as James Okoro — Cardiology.** Ask: *"What is Maria Delgado's HIV status?"* → refused. |
| **Say** | "And this isn't a legal app. Flip the domain: now the principals are **patients**. Logged in on James's chart, I ask for another patient's HIV status — refused. Identical engine, identical chokepoint — the ethical wall just became **patient confidentiality**. Changing industry is *data, not code*." |

### 2:38–2:52 — Human-in-the-loop
| | |
|---|---|
| **On screen** | Ask: *"Please set a reminder to file the motion to exclude next Friday."* A **proposed action** card appears → click **Approve** → audit shows `hitl_approved`. |
| **Say** | "And nothing acts on its own. The assistant *drafts*; a human approves — and the decision is audited. Assistants draft, attorneys decide." |

### 2:52–3:05 — Close (the proof)
| | |
|---|---|
| **On screen** | Terminal: `make evals` → **100/100**, and `pytest tests/test_isolation.py` → **1 passed**. Land on the cockpit. |
| **Say** | "The wall isn't a prompt — it's enforced in the retrieval layer, extended even to the LLM's prompt cache, and it's **measured**: every behavior scores 100 out of 100, and a guard test fails the build if a single memory ever crosses. Private memory your auditor can verify. Same engine on Qwen Cloud — or fully local, on open weights. Built on Qwen." |

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
