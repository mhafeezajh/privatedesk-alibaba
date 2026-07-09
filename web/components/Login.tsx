"use client";
import { useCallback, useEffect, useState } from "react";
import { api, storeIdentity, type Identity, type Member, type Role } from "@/lib/api";

export default function Login({ onLogin }: { onLogin: (id: Identity) => void }) {
  const [scenario, setScenario] = useState<"legal" | "healthcare">("legal");
  const [members, setMembers] = useState<Member[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const loadMembers = useCallback(async () => {
    try { setMembers(await api.members()); } catch { /* not seeded yet */ }
  }, []);
  useEffect(() => { loadMembers(); }, [loadMembers]);

  const seed = async () => {
    setErr(null); setBusy("seed");
    try { await api.seed(scenario); await loadMembers(); }
    catch { setErr("Seeding failed — is the API reachable?"); }
    finally { setBusy(null); }
  };

  const loginAs = async (mode: Role, member_id?: string) => {
    setErr(null); setBusy(member_id || mode);
    try {
      const id = await api.login(mode, member_id);
      storeIdentity(id);
      onLogin(id);
    } catch { setErr("Login failed."); setBusy(null); }
  };

  const domainLabel = scenario === "legal" ? "matters" : "patients";
  // Legal principals are "matter"s, healthcare ones are "patient"s — show only the
  // ones that belong to the selected domain (the other domain isn't seeded anyway).
  const wantRole = scenario === "legal" ? "matter" : "patient";
  const shown = members.filter((m) => m.role === wantRole);

  return (
    <main className="grid-bg flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white/85 p-6 shadow-sm backdrop-blur">
        <div className="mb-4 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white">PD</span>
          <div>
            <h1 className="text-sm font-bold text-slate-800">PrivateDesk MemoryAgent</h1>
            <p className="text-[11px] text-slate-500">sign in to a private, isolated memory</p>
          </div>
        </div>

        {/* Domain toggle */}
        <div className="mb-3">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Demo domain</div>
          <div className="grid grid-cols-2 gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1">
            {(["legal", "healthcare"] as const).map((s) => (
              <button key={s} onClick={() => setScenario(s)}
                className={["rounded-md px-3 py-1.5 text-xs font-semibold transition",
                  scenario === s ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-white"].join(" ")}>
                {s === "legal" ? "Legal — matters" : "Healthcare — patients"}
              </button>
            ))}
          </div>
          <button onClick={seed} disabled={busy === "seed"}
            className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50">
            {busy === "seed" ? "Seeding…" : shown.length ? `Reseed ${domainLabel}` : `Load ${domainLabel} demo data`}
          </button>
        </div>

        {shown.length === 0 ? (
          <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
            No {domainLabel} loaded yet — click “Load {domainLabel} demo data” above to choose an identity.
          </p>
        ) : (
          <>
            <div className="mb-1 mt-4 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Log in as a {scenario === "legal" ? "matter" : "patient"}
            </div>
            <div className="space-y-1.5">
              {shown.map((m) => (
                <button key={m.id} onClick={() => loginAs("principal", m.id)} disabled={!!busy}
                  className="flex w-full items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs hover:border-indigo-300 disabled:opacity-50">
                  <span className="inline-block h-2 w-2 rounded-full bg-indigo-500" />
                  <span className="font-medium text-slate-800">{m.name}</span>
                  <span className="ml-auto text-[10px] uppercase text-slate-400">{m.role}</span>
                </button>
              ))}
            </div>
            <p className="mt-1 text-[10px] text-slate-400">Scoped to that principal only — no access to any other.</p>

            <div className="my-3 border-t border-slate-200" />
            <div className="grid grid-cols-1 gap-1.5">
              <button onClick={() => loginAs("supervisor")} disabled={!!busy}
                className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-left text-xs font-semibold text-amber-800 hover:bg-amber-100 disabled:opacity-50">
                Log in as Compliance / Supervisor
                <span className="block text-[10px] font-normal text-amber-700">oversight — metadata only, never content</span>
              </button>
              <button onClick={() => loginAs("demo")} disabled={!!busy}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                Enter Demo mode
                <span className="block text-[10px] font-normal text-slate-500">god-view for the isolation demonstration (seed data)</span>
              </button>
            </div>
          </>
        )}

        {err && <p className="mt-3 rounded-lg bg-rose-50 px-3 py-1.5 text-xs text-rose-600">{err}</p>}
        <p className="mt-4 text-center text-[10px] text-slate-400">
          Dummy login for the demo — no password. The wall is enforced server-side regardless.
        </p>
      </div>
    </main>
  );
}
