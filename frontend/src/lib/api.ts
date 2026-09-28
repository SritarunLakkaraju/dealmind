export type Memory = {
  id: string;
  text: string;
  type: string;
  date: string | null;
  context: string | null;
  bank: string;
  label: string;
};

export type Stakeholder = { id: number; name: string; role: string; stance: string; concerns: string[] };

export type Extraction = {
  summary: string;
  objections: { text: string; category: string; raised_by: string; severity: string; resolved: boolean; how_handled: string | null }[];
  competitors: { name: string; context: string; their_claimed_price: string | null }[];
  stakeholders: { name: string; role: string; stance: string; concerns: string[] }[];
  pricing: { amount: number | null; currency: string; stated_by: string; note: string }[];
  commitments: { owner: string; who: string; what: string; due_date: string | null }[];
  next_steps: string[];
  buying_signals: string[];
  risk_signals: string[];
  sentiment: string;
};

export type Interaction = {
  id: string;
  type: "call" | "email" | "meeting" | "note";
  title: string;
  date: string;
  participants: string[];
  content: string;
  extraction: Extraction | null;
  retained: number;
};

export type Commitment = { id: number; owner: string; who: string; what: string; due_date: string | null; done: number };

type Ev = { evidence_ids: string[] };
export type Brief = {
  partial?: boolean;
  headline: string;
  deal_health: number;
  health_reason: string;
  key_risks: (Ev & { risk: string })[];
  open_commitments: (Ev & { owner: string; what: string; due: string; overdue: boolean })[];
  stakeholder_notes: (Ev & { name: string; role: string; stance: string; what_they_care_about: string })[];
  likely_objections: (Ev & { objection: string; recommended_tactic: string; why: string; confidence: string })[];
  pattern_alert: string | null;
  pattern_alert_ids: string[];
  questions_to_ask: string[];
  do_not: string[];
};

export type BriefPayload = {
  deal_id: string;
  memory: boolean;
  brief: Brief;
  citations: Record<string, Memory>;
  reflection: string;
  stats: { deal_memories: number; playbook_memories: number; seconds: number };
  generated_at: string;
};

export type Suggestion = {
  id: string;
  objection: string;
  category: string;
  tactic: string;
  outcome: string | null;
  created_at: string;
  response: CoachResponse;
};

export type Deal = {
  id: string;
  name: string;
  company: string;
  industry: string;
  amount: number;
  stage: string;
  status: "open" | "won" | "lost";
  primary_competitor: string;
  persona: string;
  next_meeting: string | null;
  description: string | null;
  closed_at: string | null;
  close_reason: string | null;
  last_touch?: string | null;
  interaction_count?: number;
  health?: number | null;
  stakeholder_count?: number;
};

export type DealDetail = Deal & {
  stakeholders: Stakeholder[];
  interactions: Interaction[];
  commitments: Commitment[];
  suggestions: Suggestion[];
  postmortem: { result: string; text: string; created_at: string } | null;
  brief: BriefPayload | null;
  brief_off: BriefPayload | null;
};

export type CoachResponse = {
  partial?: boolean;
  response_script: string;
  follow_up_question: string;
  tactic_name: string;
  objection_category: string;
  why_this_works: string;
  evidence: { memory_id: string; deal: string; outcome: string; summary: string }[];
  avoid: string[];
  confidence: string;
};

export type CoachResult = { suggestion_id: string; response: CoachResponse; citations: Record<string, Memory>; latency_ms: number };

export type TacticStat = {
  tactic: string; category: string; wins: number; losses: number; win_rate: number;
  deals: string[]; competitors: string[]; last: string;
};

export type PlaybookStats = {
  tactics: TacticStat[];
  recent: { id: number; deal_name: string; category: string; tactic: string; worked: number; note: string; date: string }[];
  total_outcomes: number;
  total_wins: number;
  postmortems: { deal_id: string; company: string; result: string; text: string; created_at: string }[];
};

export type Health = {
  memory: { backend: string; url: string | null; degraded_reason: string | null };
  llm: { configured: boolean; model: string };
  pending_retains: number;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* not json */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

const post = <T>(path: string, body: unknown) => req<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  health: () => req<Health>("/health"),
  deals: () => req<Deal[]>("/deals"),
  deal: (id: string) => req<DealDetail>(`/deals/${id}`),
  createDeal: (b: Partial<Deal>) => post<Deal>("/deals", b),
  addInteraction: (id: string, b: { type: string; title: string; date?: string; participants: string[]; content: string }) =>
    post<{ interaction_id: string; extraction: Extraction; memory_text: string }>(`/deals/${id}/interactions`, b),
  toggleCommitment: (id: string, cid: number) => post<{ id: number; done: number }>(`/deals/${id}/commitments/${cid}/toggle`, {}),
  coach: (id: string, objection: string, speaker: string) => post<CoachResult>(`/deals/${id}/coach`, { objection, speaker }),
  outcome: (sid: string, worked: boolean, note = "") =>
    post<{ ok: boolean; stats: PlaybookStats }>(`/suggestions/${sid}/outcome`, { worked, note }),
  close: (id: string, result: "won" | "lost", reason: string) =>
    post<{ analysis: string; result: string; based_on: Memory[] }>(`/deals/${id}/close`, { result, reason }),
  dealMemories: (id: string, q: string) =>
    req<{ bank: string; query: string; memories: Memory[] }>(`/deals/${id}/memories?q=${encodeURIComponent(q)}`),
  playbookMemories: (q: string) =>
    req<{ bank: string; query: string; memories: Memory[] }>(`/playbook/memories?q=${encodeURIComponent(q)}`),
  stats: () => req<PlaybookStats>("/playbook/stats"),
  ask: (question: string) => post<{ answer: string; based_on: Memory[] }>("/playbook/ask", { question }),
};

export type BriefEvent =
  | { type: "step"; key: string; label: string; counts?: Record<string, number> }
  | ({ type: "brief" } & BriefPayload)
  | { type: "error"; message: string };

export function streamBrief(dealId: string, memory: boolean, onEvent: (e: BriefEvent) => void): () => void {
  const es = new EventSource(`/api/deals/${dealId}/brief?memory=${memory ? "on" : "off"}`);
  es.onmessage = (m) => {
    const ev = JSON.parse(m.data) as BriefEvent;
    onEvent(ev);
    if (ev.type === "brief" || ev.type === "error") es.close();
  };
  es.onerror = () => {
    es.close();
    onEvent({ type: "error", message: "Connection to the server was lost." });
  };
  return () => es.close();
}
