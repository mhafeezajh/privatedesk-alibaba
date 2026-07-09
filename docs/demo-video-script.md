# PrivateDesk — Demo Video Script (Legal build)

**Target:** under 3:00 · Qwen Cloud Global AI Hackathon, Track 1 (MemoryAgent)
**Goal:** show the four scored behaviors (accumulation, isolation, forgetting, bounded recall) + human-in-the-loop, on the legal matters, running on Qwen Cloud.
**The money shot is isolation** (0:48–1:28) — give it room and let it breathe.

---

## Pre-flight (do before you hit record)

- [ ] Record against the **live Alibaba Cloud box** — open http://47.236.30.110:3000 (keep the URL visible in the recording so judges see it's deployed). `curl http://47.236.30.110:8000/health` returns `"provider":"Qwen Cloud (DashScope)"` and `"llm_ok":true`.
- [ ] On the **login screen**, keep the **Legal — matters** domain and click **Load matters demo data** once so the three matters exist: *Acme Corp v. Borealis — Litigation*, *Borealis Ltd — Employment Counsel*, *Vertex / Nimbus — M&A*, with 110+ discovery memories on the litigation matter. (Then log in as a matter to start.)
- [ ] Browser full-screen, bookmarks bar hidden, one tab only, zoom ~110% so text is legible in the recording.
- [ ] Decide your new settlement figure for the forgetting beat (script uses **$5M**).
- [ ] Record system audio off; do a voice pass after, or narrate live — your call.
- [ ] Record the **proof-of-deployment** clip separately — see [`VIDEO-SCRIPT-ALIBABA-PROOF.md`](VIDEO-SCRIPT-ALIBABA-PROOF.md) (ECS console + `/health` on the box). That's a different short clip, not part of these 3 minutes.

---

## The script

### 0:00–0:18 — Hook + premise
| | |
|---|---|
| **On screen** | The **login screen** — domain toggle + "log in as" a matter, Supervisor, or Demo. |
| **Say** | "This is PrivateDesk. Every legal matter gets its own AI assistant with private, walled-off memory — behind a login. It's running live on Alibaba Cloud, powered by Qwen — and the exact same code runs fully local on open-weight Qwen3. Because privacy isn't about where the data lives. It's isolation, open weights, and never training on it." |

### 0:18–0:48 — Accumulation (memory that persists across sessions)
| | |
|---|---|
| **On screen** | **Log in as → Acme — Litigation.** Type: *"Note for the file: our lead expert is Dr. Lena Ortiz; her deposition is next month."* Send. **Reload the page** (fresh session; you stay logged in). Ask: *"Who's our lead expert and when's the deposition?"* The assistant answers correctly. Click the **Recall trace** tab. |
| **Say** | "I log in as the Acme matter and tell its assistant a fact… then start a brand-new session. It still knows — because that fact was distilled into persistent memory, not just chat history. Here's the recall trace showing it pulled that memory back." |

### 0:48–1:35 — Isolation (the ethical wall) ← spend time here
| | |
|---|---|
| **On screen** | **Log out.** **Log in as → Borealis — Employment.** Ask: *"What's Acme's settlement position against Borealis?"* The assistant replies it has no access. (Optional: show the browser devtools Network tab — the request to the litigation matter would return **403**.) Then **Log out → Enter Demo mode** → open the **Ethical wall** tab (note the *"demonstration only"* banner): point at the **$4.2M** in the Acme pane and its **absence** in the Borealis pane. Open **Governance/Audit** → the **`isolation_block`** event. |
| **Say** | "The firm sues Borealis for Acme, and *also* advises Borealis separately — those teams must be screened. So I log in as the *Borealis* attorney and ask for Acme's settlement strategy… no access. This isn't a UI filter — the API itself returns 403 for another principal's data. In demo mode you can see both stores side by side: Acme's privileged $4.2 million ceiling lives here, and simply doesn't exist in Borealis's world — and the attempt is logged as an isolation block. If that leaked, the firm just handed the other side its strategy. The wall is enforced, not promised." |

### 1:35–2:00 — Forgetting (supersession)
| | |
|---|---|
| **On screen** | **Log in as → Acme — Litigation** (or Demo mode). Type: *"Update: the board raised the settlement ceiling to $5M."* Send. Open the **Memory store** tab — the old *$4.2M* memory now carries a **superseded** badge; the **$5M** fact is active. Ask: *"What's our current settlement ceiling?"* → answers **$5M**. (Optional: click **Run maintenance** to show the sweep.) |
| **Say** | "Memory has to stay current. I update the ceiling — and the old figure is automatically marked superseded. The assistant now acts on the new truth, and you can see the old memory greyed out, not deleted but retired." |

### 2:00–2:25 — Bounded recall at scale
| | |
|---|---|
| **On screen** | Still on **Acme — Litigation** (115 memories). Ask: *"What discovery do we have on the supply-contract timeline?"* Open the **Recall trace** tab — show the funnel: **64 retrieved → 6 into context**, with the token count, while all 115 sit in the store. |
| **Say** | "This matter holds over a hundred discovery memories. But watch the trace — out of everything stored, only the six most relevant entered the model's context, under a fixed token budget. Bounded recall: the store can grow forever; the prompt stays small." |

### 2:25–2:50 — Human-in-the-loop + close
| | |
|---|---|
| **On screen** | Ask: *"Draft a short settlement letter to opposing counsel."* A **pending action** card appears. Click **Approve**. Land on the cockpit. |
| **Say** | "And nothing leaves the building on its own — the assistant drafts, a supervising attorney approves. Same engine, two deployments: Qwen Cloud, or fully local open weights. Private memory your auditor can verify. Built on Qwen." |

---

## Tips
- If a turn is slow, the recall **trace appears first** (before the tokens) — you can talk over it.
- If you fluff a line, just pause and redo that beat; cut later. Each beat is self-contained.
- Keep the cursor deliberate — judges follow your pointer. Hover the thing you're naming.
- The single most important 10 seconds is the **side-by-side wall + the isolation_block audit**. If you nail only one beat, nail that one.
- Don't rush the close line — the "isolation, open weights, never training" framing is your thesis.
