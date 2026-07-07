"use client";
import type { AuditRow, MemoryRow, RecallTrace } from "@/lib/api";

const statusStyle: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  superseded: "bg-rose-50 text-rose-700 border-rose-200",
  expired: "bg-slate-100 text-slate-500 border-slate-200",
};

const kindStyle: Record<string, string> = {
  fact: "bg-sky-50 text-sky-700",
  preference: "bg-violet-50 text-violet-700",
  event: "bg-amber-50 text-amber-700",
  task: "bg-teal-50 text-teal-700",
  relationship: "bg-pink-50 text-pink-700",
};

const auditStyle: Record<string, string> = {
  isolation_block: "text-rose-700",
  memory_write: "text-teal-700",
  memory_recall: "text-indigo-700",
  memory_maintenance: "text-amber-700",
  hitl_approved: "text-emerald-700",
  hitl_rejected: "text-slate-600",
};

export type Tab = "memory" | "trace" | "audit";

export default function Inspector({
  tab, memories, trace, audit, onMaintenance, maintenanceMsg,
}: {
  tab: Tab;
  memories: MemoryRow[];
  trace: RecallTrace | null;
  audit: AuditRow[];
  onMaintenance: () => void;
  maintenanceMsg: string | null;
}) {
  return (
    <div className="scroll-thin h-full overflow-y-auto p-4">
      {tab === "memory" && (
        <div className="space-y-2">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Memory store · {memories.filter((m) => m.status === "active").length} active / {memories.length} total
            </span>
            <button onClick={onMaintenance}
              className="rounded-lg border border-amber-300 bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-800 hover:bg-amber-100">
              Run maintenance
            </button>
          </div>
          {maintenanceMsg && <p className="mb-2 text-[11px] text-amber-700">{maintenanceMsg}</p>}
          {memories.length === 0 && <p className="text-sm text-slate-400">No memories yet. Chat to create some.</p>}
          {memories.map((m) => (
            <div key={m.id} className={`rounded-lg border bg-white p-2.5 ${m.status !== "active" ? "opacity-70" : ""}`}>
              <div className="mb-1 flex items-center gap-1.5">
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${kindStyle[m.kind] || "bg-slate-100 text-slate-600"}`}>{m.kind}</span>
                <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${statusStyle[m.status]}`}>{m.status}</span>
                <span className="ml-auto font-mono text-[10px] text-slate-400">sal {m.salience.toFixed(2)}</span>
              </div>
              <p className={`text-[13px] ${m.status === "superseded" ? "text-slate-400 line-through" : "text-slate-700"}`}>{m.content}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "trace" && (
        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Last recall trace</span>
          {!trace ? (
            <p className="mt-3 text-sm text-slate-400">Send a message to produce a recall trace.</p>
          ) : (
            <div className="mt-3 space-y-3">
              <div className="rounded-lg bg-slate-900 p-3 font-mono text-[11px] text-slate-100">
                <div>query: <span className="text-sky-300">{trace.query}</span></div>
                <div className="mt-1 flex flex-wrap gap-x-4 text-slate-300">
                  <span>candidates: <span className="text-amber-300">{trace.candidates_considered}</span></span>
                  <span>selected: <span className="text-emerald-300">{trace.selected_count}</span></span>
                  <span>≈ tokens: <span className="text-indigo-300">{trace.approx_tokens}</span></span>
                </div>
              </div>
              {/* funnel */}
              <div className="flex items-center justify-center gap-3 text-center">
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                  <div className="text-lg font-bold text-amber-700">{trace.candidates_considered}</div>
                  <div className="text-[10px] uppercase text-amber-600">retrieved</div>
                </div>
                <span className="text-slate-400">→</span>
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2">
                  <div className="text-lg font-bold text-emerald-700">{trace.selected_count}</div>
                  <div className="text-[10px] uppercase text-emerald-600">into context</div>
                </div>
              </div>
              <div className="space-y-1.5">
                {trace.selected.map((m) => (
                  <div key={m.id} className="rounded-lg border border-slate-200 bg-white p-2">
                    <div className="mb-0.5 flex gap-3 font-mono text-[10px] text-slate-400">
                      <span>sim {m.similarity.toFixed(3)}</span>
                      <span>sal {m.salience.toFixed(2)}</span>
                      <span className="text-indigo-500">score {m.blended.toFixed(3)}</span>
                    </div>
                    <p className="text-[12px] text-slate-700">{m.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "audit" && (
        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Audit log</span>
          <div className="mt-3 space-y-1.5">
            {audit.length === 0 && <p className="text-sm text-slate-400">No events yet.</p>}
            {audit.map((a, i) => (
              <div key={i} className="flex items-start gap-2 rounded-lg border border-slate-200 bg-white p-2">
                <span className={`font-mono text-[11px] font-semibold ${auditStyle[a.event_type] || "text-slate-600"}`}>
                  {a.event_type}
                </span>
                <span className="font-mono text-[10px] text-slate-400">{new Date(a.created_at).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
