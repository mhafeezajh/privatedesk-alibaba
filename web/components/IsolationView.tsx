"use client";
import { useEffect, useState } from "react";
import { api, type Member, type MemoryRow } from "@/lib/api";

function Pane({ member }: { member: Member }) {
  const [rows, setRows] = useState<MemoryRow[]>([]);
  useEffect(() => { api.memories(member.id).then(setRows).catch(() => setRows([])); }, [member.id]);
  const active = rows.filter((r) => r.status === "active");
  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <div className="mb-2 flex items-center gap-2">
        <span className="inline-block h-2 w-2 rounded-full bg-indigo-500" />
        <span className="truncate text-sm font-semibold text-slate-700">{member.name}</span>
        <span className="ml-auto font-mono text-[10px] text-slate-400">ns: {member.id.slice(0, 8)}</span>
      </div>
      <div className="scroll-thin flex-1 space-y-1.5 overflow-y-auto rounded-lg border border-slate-200 bg-white/70 p-2">
        {active.length === 0 && <p className="p-2 text-xs text-slate-400">No active memories.</p>}
        {active.map((m) => (
          <div key={m.id} className="rounded-md border border-slate-100 bg-white p-2">
            <span className="text-[10px] font-semibold text-teal-600">{m.kind}</span>
            <p className="text-[12px] text-slate-700">{m.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function IsolationView({ members }: { members: Member[] }) {
  const [left, setLeft] = useState(0);
  const [right, setRight] = useState(1);
  if (members.length < 2) return <p className="p-4 text-sm text-slate-400">Seed the demo to compare two matters.</p>;

  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ethical wall — two matters, side by side</span>
        <span className="ml-auto rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700">
          screened · isolated
        </span>
      </div>
      <div className="mb-3 flex gap-2">
        <select value={left} onChange={(e) => setLeft(+e.target.value)}
          className="flex-1 rounded-lg border border-slate-300 px-2 py-1 text-xs">
          {members.map((m, i) => <option key={m.id} value={i}>{m.name}</option>)}
        </select>
        <select value={right} onChange={(e) => setRight(+e.target.value)}
          className="flex-1 rounded-lg border border-slate-300 px-2 py-1 text-xs">
          {members.map((m, i) => <option key={m.id} value={i}>{m.name}</option>)}
        </select>
      </div>
      <div className="flex flex-1 gap-0 overflow-hidden">
        <Pane member={members[left]} />
        {/* the wall */}
        <div className="mx-3 flex w-px flex-col items-center justify-center bg-gradient-to-b from-transparent via-amber-400 to-transparent">
          <span className="rotate-90 whitespace-nowrap rounded bg-amber-100 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-amber-700">
            isolated
          </span>
        </div>
        <Pane member={members[right]} />
      </div>
    </div>
  );
}
