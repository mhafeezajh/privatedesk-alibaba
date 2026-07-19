// Typed client for the PrivateDesk MemoryAgent API, including SSE chat streaming.

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type Member = { id: string; name: string; role: string; persona_key: string };

export type MemoryRow = {
  id: string; kind: string; content: string; salience: number;
  status: "active" | "superseded" | "expired";
  superseded_by: string | null; created_at: string; last_used_at: string | null;
};

export type TraceMemory = {
  id: string; kind: string; content: string;
  salience: number; similarity: number; blended: number;
};

export type RecallTrace = {
  query: string; candidates_considered: number; selected_count: number;
  approx_tokens: number; token_budget: number; selected: TraceMemory[];
};

export type AuditRow = { event_type: string; detail: Record<string, unknown>; created_at: string };

export type PromptRow = {
  member_id: string; kind: string; model: string; base_url: string;
  provider: string; messages: { role: string; content: string }[]; created_at: string;
};

export type GovReport = {
  principal: { name: string; role: string; persona: string; namespace: string };
  generated_at: string;
  memories: { total: number; active: number; superseded: number; expired: number; by_kind: Record<string, number> };
  audit: { total_events: number; by_type: Record<string, number> };
  governance: {
    isolation_blocks: number; memory_writes: number; memory_recalls: number;
    maintenance_runs: number; hitl_approved: number; hitl_rejected: number; actions_pending: number;
  };
  attestation: { namespace_isolated: boolean; human_in_the_loop: boolean; statement: string };
};
export type PendingAction = { id: string; action_type: string; payload: Record<string, unknown> };

export type Role = "principal" | "supervisor" | "demo";
export type Identity = { token: string; role: Role; member_id: string | null; name: string | null };

export type OverviewRow = {
  id: string; name: string; role: string; namespace: string;
  memories_active: number; memories_total: number;
  isolation_blocks: number; audit_events: number; attestation_ok: boolean;
};
export type GovOverview = {
  generated_at: string;
  principals: OverviewRow[];
  totals: { principals: number; isolation_blocks: number };
  note: string;
};

// ── auth token (in-memory + localStorage) ────────────────────────────────────
let TOKEN: string | null = null;
export function setToken(t: string | null) {
  TOKEN = t;
  if (typeof window !== "undefined") {
    if (t) localStorage.setItem("pd_token", t); else localStorage.removeItem("pd_token");
  }
}
export function loadStoredIdentity(): Identity | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("pd_identity");
  if (!raw) return null;
  try {
    const id = JSON.parse(raw) as Identity;
    TOKEN = id.token;
    return id;
  } catch { return null; }
}
export function storeIdentity(id: Identity | null) {
  setToken(id?.token ?? null);
  if (typeof window !== "undefined") {
    if (id) localStorage.setItem("pd_identity", JSON.stringify(id));
    else localStorage.removeItem("pd_identity");
  }
}

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  login: (mode: Role, member_id?: string) => j<Identity>("/api/auth/login", { method: "POST", body: JSON.stringify({ mode, member_id }) }),
  overview: () => j<GovOverview>("/api/inspector/overview"),
  members: () => j<Member[]>("/api/members"),
  startSession: (member_id: string) => j<{ session_id: string }>("/api/session/start", { method: "POST", body: JSON.stringify({ member_id }) }),
  memories: (member_id: string) => j<MemoryRow[]>(`/api/inspector/memories?member_id=${member_id}`),
  audit: (member_id: string) => j<AuditRow[]>(`/api/inspector/audit?member_id=${member_id}`),
  prompts: (member_id: string) => j<PromptRow[]>(`/api/inspector/prompts?member_id=${member_id}`),
  maintenance: (member_id: string) => j<{ expired: number; pruned: number }>(`/api/inspector/maintenance?member_id=${member_id}`, { method: "POST" }),
  report: (member_id: string) => j<GovReport>(`/api/inspector/report?member_id=${member_id}`),
  pending: (member_id: string) => j<PendingAction[]>(`/api/actions/pending?member_id=${member_id}`),
  approve: (id: string) => j(`/api/actions/${id}/approve`, { method: "POST" }),
  reject: (id: string) => j(`/api/actions/${id}/reject`, { method: "POST" }),
  seed: (scenario: string = "legal") => j<{ scenario: string; org: string; members: Member[]; bulk_member: string; bulk_memories_created: number }>("/api/demo/seed", { method: "POST", body: JSON.stringify({ scenario }) }),
};

export type ChatHandlers = {
  onTrace?: (t: RecallTrace) => void;
  onToken?: (tok: string) => void;
  onProposedAction?: (a: PendingAction) => void;
  onDone?: () => void;
  onError?: (e: unknown) => void;
};

// POST + ReadableStream SSE parser (EventSource can't POST).
export async function streamChat(session_id: string, message: string, h: ChatHandlers) {
  try {
    const res = await fetch(`${BASE}/api/chat`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
      },
      body: JSON.stringify({ session_id, message }),
    });
    if (!res.body) throw new Error("no stream body");
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const frames = buf.split("\n\n");
      buf = frames.pop() || "";
      for (const frame of frames) {
        let ev = "message";
        let data = "";
        for (const line of frame.split("\n")) {
          if (line.startsWith("event:")) ev = line.slice(6).trim();
          else if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;
        try {
          const parsed = JSON.parse(data);
          if (ev === "trace") h.onTrace?.(parsed);
          else if (ev === "proposed_action") h.onProposedAction?.(parsed);
          else if (ev === "done") h.onDone?.();
          else if (parsed.token != null) h.onToken?.(parsed.token);
        } catch { /* ignore malformed frame */ }
      }
    }
    h.onDone?.();
  } catch (e) {
    h.onError?.(e);
  }
}
