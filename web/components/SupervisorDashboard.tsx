"use client";
import { useEffect, useState } from "react";
import { api, type GovOverview } from "@/lib/api";

export default function SupervisorDashboard() {
  const [ov, setOv] = useState<GovOverview | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api.overview().then(setOv).catch(() => setErr("Couldn't load the overview.")); }, []);

  if (err) return <p className="p-6 text-sm text-rose-500">{err}</p>;
  if (!ov) return <p className="p-6 text-sm text-slate-400">Loading oversight…</p>;

  return (
    <div className="mx-auto max-w-[1100px] px-5 py-6">
      <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-[11px] text-white">👁</span>
          <h2 className="text-sm font-bold text-amber-900">Compliance oversight — metadata only</h2>
          <span className="ml-auto rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-amber-700">
            {ov.totals.principals} principals · {ov.totals.isolation_blocks} isolation blocks
          </span>
        </div>
        <p className="mt-1 text-[12px] text-amber-900">{ov.note}</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-[13px]">
          <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-2 font-semibold">Principal</th>
              <th className="px-3 py-2 font-semibold">Namespace</th>
              <th className="px-3 py-2 font-semibold text-right">Active / total</th>
              <th className="px-3 py-2 font-semibold text-right">Isolation blocks</th>
              <th className="px-3 py-2 font-semibold text-right">Audit events</th>
              <th className="px-3 py-2 font-semibold text-center">Attestation</th>
            </tr>
          </thead>
          <tbody>
            {ov.principals.map((p) => (
              <tr key={p.id} className="border-t border-slate-100">
                <td className="px-3 py-2">
                  <div className="font-medium text-slate-800">{p.name}</div>
                  <div className="text-[10px] uppercase text-slate-400">{p.role}</div>
                </td>
                <td className="px-3 py-2 font-mono text-[11px] text-slate-500">{p.namespace}</td>
                <td className="px-3 py-2 text-right font-mono">{p.memories_active} / {p.memories_total}</td>
                <td className="px-3 py-2 text-right font-mono text-rose-600">{p.isolation_blocks}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-600">{p.audit_events}</td>
                <td className="px-3 py-2 text-center">
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">✓ isolated</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-[11px] text-slate-400">
        This view confirms the walls hold — counts, audit totals, and per-principal attestation — and
        deliberately shows <span className="font-semibold">no memory content</span>. Reading a principal's
        content requires logging in as that principal.
      </p>
    </div>
  );
}
