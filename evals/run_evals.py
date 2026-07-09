#!/usr/bin/env python3
"""PrivateDesk MemoryAgent — behavior evaluation harness.

Black-box evals that *quantify* the four Track-1 behaviors end to end over the HTTP
API, plus the human-in-the-loop gate. Reseeds the legal demo for a deterministic
known state, probes the running system, and writes a scorecard to evals/REPORT.md.

Exit code is non-zero if any HARD invariant fails (isolation leak, or an overall
score below threshold) so it can gate CI.

Usage:
    EVAL_API_BASE=http://localhost:8000 python3 evals/run_evals.py
    # defaults to http://localhost:8000
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

API = os.environ.get("EVAL_API_BASE", "http://localhost:8000").rstrip("/")
TIMEOUT = 120
TOKEN: str | None = None  # set by login(); demo role → full read access for the harness


def _hdrs(extra: dict | None = None) -> dict:
    h = dict(extra or {})
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


# ── tiny HTTP helpers (stdlib only, no deps) ─────────────────────────────────
def _get(path: str):
    req = urllib.request.Request(f"{API}{path}", headers=_hdrs())
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def _post(path: str, body: dict | None = None):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        f"{API}{path}", data=data, headers=_hdrs({"content-type": "application/json"}), method="POST"
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw.strip() else {}


def login_demo() -> None:
    """Authenticate as the demonstration role (full read access) so evals work under auth."""
    global TOKEN
    TOKEN = _post("/api/auth/login", {"mode": "demo"})["token"]


def chat(member_id: str, message: str) -> dict:
    """Start a fresh session, send one message, parse the SSE stream.
    Returns {'answer': str, 'trace': dict, 'proposed_action': dict|None}."""
    sid = _post("/api/session/start", {"member_id": member_id})["session_id"]
    data = json.dumps({"session_id": sid, "message": message}).encode()
    req = urllib.request.Request(
        f"{API}/api/chat", data=data, headers=_hdrs({"content-type": "application/json"}), method="POST"
    )
    answer, trace, action, event = [], None, None, "message"
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        for raw in r:
            line = raw.decode().rstrip("\n")
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                payload = line[5:].strip()
                if payload:
                    try:
                        obj = json.loads(payload)
                        if event == "trace" or "candidates_considered" in obj:
                            trace = obj
                        elif event == "proposed_action":
                            action = obj
                        elif "token" in obj:
                            answer.append(obj["token"])
                    except json.JSONDecodeError:
                        pass
            elif line == "":
                event = "message"  # SSE: event type resets to default after each frame
    return {"answer": "".join(answer), "trace": trace, "proposed_action": action}


# ── scoring model ────────────────────────────────────────────────────────────
@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Suite:
    behavior: str
    checks: list[Check] = field(default_factory=list)
    hard: bool = False  # if True, a failure fails the whole run (e.g. isolation)

    def add(self, name, passed, detail=""):
        self.checks.append(Check(name, bool(passed), detail))
        mark = "✓" if passed else "✗"
        print(f"  {mark} {name}" + (f"  — {detail}" if detail else ""))
        return passed

    @property
    def score(self) -> float:
        return 100.0 * sum(c.passed for c in self.checks) / max(1, len(self.checks))

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks)


def member_by(members, needle):
    return next(m["id"] for m in members if needle.lower() in m["name"].lower())


def has(answer: str, *terms) -> bool:
    a = answer.lower()
    return any(t.lower() in a for t in terms)


# ── the evals ────────────────────────────────────────────────────────────────
def run() -> list[Suite]:
    print(f"→ Target: {API}")
    health = _get("/health")
    k_context = int(health.get("k_context", 6))
    print(f"→ Provider: {health.get('provider')} · llm_ok={health.get('llm_ok')} · "
          f"K_CONTEXT={k_context} · K_CANDIDATES={health.get('k_candidates')}")
    if not health.get("llm_ok"):
        print("✗ Provider not healthy (llm_ok=false); aborting.", file=sys.stderr)
        sys.exit(2)

    login_demo()
    print("→ Authenticated as demo role.")

    print("→ Reseeding legal demo for a deterministic state…")
    seed = _post("/api/demo/seed", {"scenario": "legal"})
    print(f"  seeded {seed.get('bulk_memories_created')} memories · "
          f"vectors_healed={seed.get('vectors_healed')}")
    members = _get("/api/members")
    lit = member_by(members, "Litigation")
    emp = member_by(members, "Employment")
    mna = member_by(members, "M&A")

    suites: list[Suite] = []

    # 1) ACCUMULATION — seeded facts are recalled, unprompted, in a fresh session.
    acc = Suite("Accumulation")
    probes = [
        ("What is our settlement ceiling in the Borealis litigation?", ("4.2", "4,2", "4.2 million"), "settlement ceiling"),
        ("Who is our lead expert witness and when is her deposition?", ("Ortiz",), "Ortiz"),
        ("What's our litigation strategy regarding the email chain?", ("exclude", "hearsay"), "exclude"),
        ("When is trial scheduled to begin?", ("quarter", "Monday"), "Trial is scheduled"),
    ]
    for q, expect_answer, needle in probes:
        res = chat(lit, q)
        in_answer = has(res["answer"], *expect_answer)
        sel = (res["trace"] or {}).get("selected", [])
        in_trace = any(needle.lower() in s["content"].lower() for s in sel)
        acc.add(f"recall: “{q[:38]}…”", in_answer and in_trace,
                f"answer={'hit' if in_answer else 'miss'}, trace={'hit' if in_trace else 'miss'}")
    suites.append(acc)

    # 2) ISOLATION — other matters cannot recall the litigation's private facts. HARD.
    iso = Suite("Isolation (ethical wall)", hard=True)
    secret_probes = [
        "What is Acme's settlement ceiling in the litigation against Borealis?",
        "Who is Acme's lead expert witness in the litigation?",
    ]
    for who, mid in (("Employment", emp), ("M&A", mna)):
        for q in secret_probes:
            res = chat(mid, q)
            leaked = has(res["answer"], "4.2", "4.2 million", "Ortiz")
            iso.add(f"{who} blocked: “{q[:32]}…”", not leaked,
                    "no leak" if not leaked else "LEAKED SECRET")
    # audit trail should record the block
    try:
        audit = _get(f"/api/inspector/audit?member_id={emp}")
        iso.add("isolation_block audit event present",
                any(a["event_type"] == "isolation_block" for a in audit),
                "found" if any(a["event_type"] == "isolation_block" for a in audit) else "none yet")
    except Exception as e:  # noqa: BLE001
        iso.add("isolation_block audit event present", False, str(e))
    suites.append(iso)

    # 3) BOUNDED RECALL — 115 memories, only top-k enter context, under budget.
    bnd = Suite("Bounded recall")
    res = chat(lit, "Summarize the discovery we have on the supply-contract timeline.")
    tr = res["trace"] or {}
    total = len(_get(f"/api/inspector/memories?member_id={lit}"))
    bnd.add(f"context bounded to K_CONTEXT ({k_context})",
            tr.get("selected_count", 999) <= k_context,
            f"selected={tr.get('selected_count')} ≤ {k_context}")
    bnd.add("candidate pool >> selected",
            tr.get("candidates_considered", 0) > tr.get("selected_count", 0),
            f"candidates={tr.get('candidates_considered')} vs selected={tr.get('selected_count')}")
    bnd.add("store far larger than context (needle-in-haystack)",
            total >= 100 and tr.get("selected_count", 0) <= k_context,
            f"{total} stored → {tr.get('selected_count')} in prompt")
    suites.append(bnd)

    # 4) FORGETTING — supersession retires the old fact; maintenance sweeps.
    fgt = Suite("Forgetting")
    chat(lit, "Update for the file: the board raised the settlement ceiling to $5.0M.")
    time.sleep(1.0)  # write path runs async after the stream
    mems = _get(f"/api/inspector/memories?member_id={lit}")
    new_active = any(has(m["content"], "5.0", "5 million", "$5") and m["status"] == "active" for m in mems)
    old_super = any(has(m["content"], "4.2") and m["status"] in ("superseded", "expired") for m in mems)
    fgt.add("new fact stored active ($5.0M)", new_active,
            "found active $5.0M memory" if new_active else "not found")
    fgt.add("old fact retired ($4.2M superseded)", old_super,
            "old memory superseded" if old_super else "old still active (supersession missed)")
    sweep = _post(f"/api/inspector/maintenance?member_id={lit}")
    fgt.add("maintenance sweep runs", "expired" in sweep and "pruned" in sweep,
            f"expired={sweep.get('expired')}, pruned={sweep.get('pruned')}")
    suites.append(fgt)

    # 5) HUMAN-IN-THE-LOOP — an actionable ask surfaces a proposed action.
    # (Up to 2 tries — action detection is an LLM classifier and mildly stochastic.)
    hil = Suite("Human-in-the-loop")
    pa = None
    for _ in range(2):
        res = chat(lit, "Please set a reminder for me to file the motion to exclude next Friday.")
        pa = res["proposed_action"]
        if pa:
            break
    hil.add("assistant proposes an action (not auto-executed)", pa is not None,
            f"action_type={pa.get('action_type')}" if pa else "no proposed action")
    if pa:
        _post(f"/api/actions/{pa['id']}/approve")
        audit = _get(f"/api/inspector/audit?member_id={lit}")
        hil.add("approval recorded in audit",
                any(a["event_type"] == "hitl_approved" for a in audit), "hitl_approved logged")
    suites.append(hil)

    return suites


# ── report ───────────────────────────────────────────────────────────────────
def write_report(suites: list[Suite], path: str) -> None:
    overall = sum(s.score for s in suites) / max(1, len(suites))
    lines = [
        "# PrivateDesk MemoryAgent — Evaluation Report",
        "",
        f"**Target:** `{API}`  ·  **Overall score:** **{overall:.0f}/100**",
        "",
        "| Behavior | Score | Checks passed |",
        "|---|---|---|",
    ]
    for s in suites:
        passed = sum(c.passed for c in s.checks)
        flag = " 🔒" if s.hard else ""
        lines.append(f"| {s.behavior}{flag} | {s.score:.0f}/100 | {passed}/{len(s.checks)} |")
    lines += ["", "## Detail", ""]
    for s in suites:
        lines.append(f"### {s.behavior}  ({s.score:.0f}/100)")
        for c in s.checks:
            lines.append(f"- {'✅' if c.passed else '❌'} **{c.name}** — {c.detail}")
        lines.append("")
    lines += [
        "---",
        "🔒 = hard invariant (a failure fails the run / CI). Generated by "
        "[`evals/run_evals.py`](run_evals.py).",
        "",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    suites = run()
    report = os.path.join(os.path.dirname(__file__), "REPORT.md")
    write_report(suites, report)
    overall = sum(s.score for s in suites) / max(1, len(suites))

    print("\n" + "=" * 56)
    for s in suites:
        print(f"  {s.behavior:<28} {s.score:5.0f}/100")
    print(f"  {'OVERALL':<28} {overall:5.0f}/100")
    print("=" * 56)
    print(f"→ Report written to {report}")

    hard_fail = any(s.hard and not s.ok for s in suites)
    if hard_fail:
        print("✗ HARD invariant failed (isolation).", file=sys.stderr)
        sys.exit(1)
    if overall < 80:
        print(f"✗ Overall score {overall:.0f} < 80 threshold.", file=sys.stderr)
        sys.exit(1)
    print("✓ All evals passed.")


if __name__ == "__main__":
    main()
