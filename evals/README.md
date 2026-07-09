# Evals — quantifying the four behaviors

Black-box evaluation harness that scores PrivateDesk's Track-1 behaviors end to end over the
HTTP API, plus the human-in-the-loop gate. It reseeds the legal demo for a deterministic state,
probes the running system, prints a scorecard, and writes [`REPORT.md`](REPORT.md).

## What it measures

| Suite | Checks |
|---|---|
| **Accumulation** | seeded facts are recalled (answer + recall-trace) in fresh sessions |
| **Isolation** 🔒 | other matters cannot recall a matter's private facts; `isolation_block` is audited |
| **Bounded recall** | context is bounded to `K_CONTEXT`; candidate pool ≫ selected; 100+ stored → few in prompt |
| **Forgetting** | a superseding fact retires the old one; the maintenance sweep runs |
| **Human-in-the-loop** | an actionable ask surfaces a *proposed* action; approval is audited |

🔒 = hard invariant. The run **exits non-zero** if isolation leaks or the overall score < 80, so
it can gate CI.

## Run it

```bash
# against a local stack:
python3 evals/run_evals.py

# against the live deployment:
EVAL_API_BASE=http://<host>:8000 python3 evals/run_evals.py
```

No dependencies (stdlib only). Needs a healthy provider (`/health` → `llm_ok: true`); the harness
reseeds the demo, so run it against a demo/test box, not production data.

## Automating later (optional)

The harness exits non-zero on any isolation leak or a low overall score, so it drops cleanly into
CI when wanted: bring up `postgres qdrant redis api` (with a `DASHSCOPE_API_KEY` **secret**), wait
for `/health` → `llm_ok:true`, then run `python3 evals/run_evals.py`. Not wired up right now.
