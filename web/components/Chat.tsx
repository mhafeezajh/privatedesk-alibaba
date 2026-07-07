"use client";
import { useEffect, useRef, useState } from "react";
import type { Member, PendingAction } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };

const personaTone: Record<string, string> = {
  litigation_assistant: "Litigation",
  employment_assistant: "Employment",
  corporate_assistant: "Corporate / M&A",
};

export default function Chat({
  member, messages, streaming, pending, onSend, onApprove, onReject,
}: {
  member: Member | null;
  messages: Msg[];
  streaming: boolean;
  pending: PendingAction[];
  onSend: (text: string) => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, pending]);

  const send = () => {
    const t = text.trim();
    if (!t || streaming || !member) return;
    onSend(t);
    setText("");
  };

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white/80 shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
        <span className="inline-block h-2 w-2 rounded-full bg-indigo-500" />
        <h2 className="text-sm font-semibold text-slate-700">
          {member ? `Working on ${member.name}` : "Pick a matter"}
        </h2>
        {member && (
          <span className="ml-auto rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-700">
            {personaTone[member.persona_key] || member.persona_key}
          </span>
        )}
      </div>

      <div className="scroll-thin flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <p className="mt-8 text-center text-sm text-slate-400">
            Add facts to {member?.name || "this matter"}. They stay inside this matter — nothing crosses to another.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div className={[
              "max-w-[80%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed",
              m.role === "user"
                ? "bg-indigo-600 text-white"
                : "border border-slate-200 bg-slate-50 text-slate-800",
            ].join(" ")}>
              {m.content || (streaming && i === messages.length - 1 ? <span className="caret" /> : "")}
              {m.role === "assistant" && streaming && i === messages.length - 1 && m.content ? <span className="caret" /> : null}
            </div>
          </div>
        ))}

        {pending.map((a) => (
          <div key={a.id} className="rounded-xl border border-amber-300 bg-amber-50 p-3">
            <div className="mb-1 flex items-center gap-2">
              <span className="rounded bg-amber-200 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-800">
                Needs approval
              </span>
              <span className="text-xs font-semibold text-amber-900">{a.action_type.replace("_", " ")}</span>
            </div>
            <pre className="mb-2 whitespace-pre-wrap font-mono text-[11px] text-amber-900/80">
              {JSON.stringify(a.payload, null, 2)}
            </pre>
            <div className="flex gap-2">
              <button onClick={() => onApprove(a.id)}
                className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-700">
                Approve
              </button>
              <button onClick={() => onReject(a.id)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50">
                Reject
              </button>
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="border-t border-slate-200 p-3">
        <div className="flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") send(); }}
            disabled={!member || streaming}
            placeholder={member ? `Add to ${member.name}…` : "Select a matter first"}
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 disabled:bg-slate-50"
          />
          <button onClick={send} disabled={!member || streaming || !text.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-40">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
