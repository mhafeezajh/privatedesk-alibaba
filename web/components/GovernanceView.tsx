"use client";
import { useEffect, useState } from "react";
import { api, type GovReport, type Member } from "@/lib/api";

function Stat({ label, value, tone = "slate" }: { label: string; value: number | string; tone?: string }) {
  const tones: Record<string, string> = {
    slate: "text-slate-800",
    emerald: "text-emerald-700",
    rose: "text-rose-700",
    indigo: "text-indigo-700",
    amber: "text-amber-700",
  };
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-2.5">
      <div className={`text-xl font-bold ${tones[tone]}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  );
}

export default function GovernanceView({ member }: { member: Member | null }) {
  const [rep, setRep] = useState<GovReport | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!member) return;
    setRep(null);
    setErr(null);
    api.report(member.id).then(setRep).catch(() => setErr("Couldn't load the report."));
  }, [member?.id]);

  if (!member) return <p className="p-4 text-sm text-slate-400">Select a principal to see its governance report.</p>;
  if (err) return <p className="p-4 text-sm text-rose-500">{err}</p>;
  if (!rep) return <p className="p-4 text-sm text-slate-400">Loading report…</p>;

  const download = () => {
    const blob = new Blob([JSON.stringify(rep, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `compliance-${rep.principal.name.replace(/[^a-z0-9]+/gi, "_")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const g = rep.governance;
  return (
    <div className="scroll-thin h-full overflow-y-auto p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Governance &amp; compliance
        </span>
        <button onClick={download}
          className="ml-auto rounded-lg border border-indigo-300 bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-700 hover:bg-indigo-100">
          ⭳ Download report
        </button>
      </div>

      {/* Attestation banner */}
      <div className="mb-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3">
        <div className="mb-1 flex items-center gap-2">
          <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-emerald-600 text-[10px] text-white">✓</span>
          <span className="text-xs font-semibold text-emerald-800">Isolation attestation</span>
          <span className="ml-auto font-mono text-[10px] text-emerald-700">ns: {rep.principal.namespace}</span>
        </div>
        <p className="text-[12px] leading-snug text-emerald-900">{rep.attestation.statement}</p>
      </div>

      {/* Governance counters */}
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Controls exercised</div>
      <div className="mb-3 grid grid-cols-3 gap-2">
        <Stat label="Isolation blocks" value={g.isolation_blocks} tone="rose" />
        <Stat label="HITL approved" value={g.hitl_approved} tone="emerald" />
        <Stat label="HITL rejected" value={g.hitl_rejected} tone="slate" />
        <Stat label="Memory writes" value={g.memory_writes} tone="indigo" />
        <Stat label="Recalls" value={g.memory_recalls} tone="indigo" />
        <Stat label="Maintenance runs" value={g.maintenance_runs} tone="amber" />
      </div>

      {/* Memory state */}
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Memory state</div>
      <div className="mb-3 grid grid-cols-4 gap-2">
        <Stat label="Total" value={rep.memories.total} />
        <Stat label="Active" value={rep.memories.active} tone="emerald" />
        <Stat label="Superseded" value={rep.memories.superseded} tone="rose" />
        <Stat label="Expired" value={rep.memories.expired} tone="slate" />
      </div>

      {/* Audit breakdown */}
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        Audit trail · {rep.audit.total_events} events
      </div>
      <div className="space-y-1">
        {Object.entries(rep.audit.by_type).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
          <div key={k} className="flex items-center gap-2 rounded-md border border-slate-100 bg-white px-2 py-1">
            <span className="font-mono text-[11px] text-slate-600">{k}</span>
            <span className="ml-auto font-mono text-[11px] font-semibold text-slate-800">{v}</span>
          </div>
        ))}
      </div>

      <p className="mt-3 text-[10px] text-slate-400">
        Generated {new Date(rep.generated_at).toLocaleString()} · scoped to this principal's namespace
      </p>
    </div>
  );
}
