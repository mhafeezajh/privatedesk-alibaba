"use client";
import { useCallback, useEffect, useState } from "react";
import { api, streamChat, type AuditRow, type Member, type MemoryRow, type PendingAction, type RecallTrace } from "@/lib/api";
import Chat from "@/components/Chat";
import Inspector, { type Tab } from "@/components/Inspector";
import IsolationView from "@/components/IsolationView";
import GovernanceView from "@/components/GovernanceView";

type Msg = { role: "user" | "assistant"; content: string };
type RightView = Tab | "isolation" | "governance";

export default function Page() {
  const [members, setMembers] = useState<Member[]>([]);
  const [selected, setSelected] = useState<Member | null>(null);
  const [sessions, setSessions] = useState<Record<string, string>>({});
  const [threads, setThreads] = useState<Record<string, Msg[]>>({});
  const [streaming, setStreaming] = useState(false);

  const [trace, setTrace] = useState<RecallTrace | null>(null);
  const [memories, setMemories] = useState<MemoryRow[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [pending, setPending] = useState<PendingAction[]>([]);
  const [view, setView] = useState<RightView>("memory");
  const [scenario, setScenario] = useState<"legal" | "healthcare">("legal");
  const [maintMsg, setMaintMsg] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);

  const loadMembers = useCallback(async () => {
    try { setMembers(await api.members()); } catch { setBanner("Can't reach the API. Is it running on :8000?"); }
  }, []);
  useEffect(() => { loadMembers(); }, [loadMembers]);

  const refreshInspector = useCallback(async (m: Member) => {
    const [mem, aud, pend] = await Promise.all([api.memories(m.id), api.audit(m.id), api.pending(m.id)]);
    setMemories(mem); setAudit(aud); setPending(pend);
  }, []);

  const selectMember = useCallback(async (m: Member) => {
    setSelected(m);
    setMaintMsg(null);
    if (!sessions[m.id]) {
      try { const { session_id } = await api.startSession(m.id); setSessions((s) => ({ ...s, [m.id]: session_id })); }
      catch { setBanner("Couldn't start a session."); }
    }
    refreshInspector(m).catch(() => {});
  }, [sessions, refreshInspector]);

  const send = useCallback(async (text: string) => {
    if (!selected) return;
    const sid = sessions[selected.id];
    if (!sid) return;
    const mid = selected.id;
    setThreads((t) => ({ ...t, [mid]: [...(t[mid] || []), { role: "user", content: text }, { role: "assistant", content: "" }] }));
    setStreaming(true);
    setTrace(null);
    await streamChat(sid, text, {
      onTrace: (tr) => { setTrace(tr); setView("trace"); },
      onToken: (tok) => setThreads((t) => {
        const arr = [...(t[mid] || [])];
        arr[arr.length - 1] = { role: "assistant", content: arr[arr.length - 1].content + tok };
        return { ...t, [mid]: arr };
      }),
      onProposedAction: (a) => setPending((p) => [...p, a]),
      onDone: () => { setStreaming(false); if (selected) refreshInspector(selected).catch(() => {}); },
      onError: () => { setStreaming(false); setBanner("Stream error during chat."); },
    });
  }, [selected, sessions, refreshInspector]);

  const resolve = useCallback(async (id: string, kind: "approve" | "reject") => {
    await (kind === "approve" ? api.approve(id) : api.reject(id));
    setPending((p) => p.filter((a) => a.id !== id));
    if (selected) refreshInspector(selected).catch(() => {});
  }, [selected, refreshInspector]);

  const maintenance = useCallback(async () => {
    if (!selected) return;
    const r = await api.maintenance(selected.id);
    setMaintMsg(`Swept: ${r.expired} expired, ${r.pruned} pruned.`);
    refreshInspector(selected).catch(() => {});
  }, [selected, refreshInspector]);

  const seed = useCallback(async () => {
    setBanner(null);
    try {
      const r = await api.seed(scenario);
      await loadMembers();
      setBanner(`Seeded ${r.org} · ${r.members.length} principals · ${r.bulk_memories_created} memories.`);
      setSelected(null); setSessions({}); setThreads({}); setTrace(null);
      setMemories([]); setAudit([]); setPending([]);
    } catch { setBanner("Seed failed — check the API."); }
  }, [loadMembers, scenario]);

  const tabs: { id: RightView; label: string }[] = [
    { id: "memory", label: "Memory store" },
    { id: "trace", label: "Recall trace" },
    { id: "audit", label: "Audit log" },
    { id: "isolation", label: "Ethical wall" },
    { id: "governance", label: "Governance" },
  ];

  return (
    <main className="grid-bg min-h-screen">
      <header className="border-b border-slate-200 bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-3 px-5 py-3">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white">PD</span>
            <div>
              <h1 className="text-sm font-bold leading-tight text-slate-800">PrivateDesk MemoryAgent</h1>
              <p className="text-[11px] leading-tight text-slate-500">matter-isolated memory · the ethical wall, enforced</p>
            </div>
          </div>

          <div className="ml-2 flex flex-wrap items-center gap-1.5">
            {members.map((m) => (
              <button key={m.id} onClick={() => selectMember(m)}
                className={[
                  "rounded-full px-3 py-1 text-xs font-medium transition",
                  selected?.id === m.id
                    ? "bg-indigo-600 text-white"
                    : "border border-slate-300 bg-white text-slate-600 hover:border-indigo-300",
                ].join(" ")}>
                {m.name}
              </button>
            ))}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <select value={scenario} onChange={(e) => setScenario(e.target.value as "legal" | "healthcare")}
              className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs font-medium text-slate-600">
              <option value="legal">Legal — matters</option>
              <option value="healthcare">Healthcare — patients</option>
            </select>
            <button onClick={seed}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50">
              Seed demo
            </button>
          </div>
        </div>
        {banner && (
          <div className="mx-auto max-w-[1400px] px-5 pb-2">
            <div className="rounded-lg bg-indigo-50 px-3 py-1.5 text-xs text-indigo-700">{banner}</div>
          </div>
        )}
      </header>

      <div className="mx-auto grid max-w-[1400px] gap-4 px-5 py-5 lg:grid-cols-[minmax(380px,2fr)_3fr]" style={{ height: "calc(100vh - 76px)" }}>
        <div className="min-h-0">
          <Chat
            member={selected}
            messages={selected ? threads[selected.id] || [] : []}
            streaming={streaming}
            pending={pending}
            onSend={send}
            onApprove={(id) => resolve(id, "approve")}
            onReject={(id) => resolve(id, "reject")}
          />
        </div>

        <div className="flex min-h-0 flex-col rounded-xl border border-slate-200 bg-white/80 shadow-sm">
          <div className="flex items-center gap-1 border-b border-slate-200 px-2 py-2">
            {tabs.map((t) => (
              <button key={t.id} onClick={() => setView(t.id)}
                className={[
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                  view === t.id ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-100",
                ].join(" ")}>
                {t.label}
              </button>
            ))}
            <span className="ml-auto pr-2 text-[11px] text-slate-400">
              {selected ? `inspecting ${selected.name}` : "no principal selected"}
            </span>
          </div>
          <div className="min-h-0 flex-1">
            {view === "isolation"
              ? <IsolationView members={members} />
              : view === "governance"
              ? <GovernanceView member={selected} />
              : <Inspector tab={view} memories={memories} trace={trace} audit={audit} onMaintenance={maintenance} maintenanceMsg={maintMsg} />}
          </div>
        </div>
      </div>
    </main>
  );
}
