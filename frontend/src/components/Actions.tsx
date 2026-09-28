import clsx from "clsx";
import {
  Ban, BookOpen, Brain, CheckCircle2, Database, Gavel, Mic, Quote, Search, Send, ThumbsDown, ThumbsUp, Timer, Trophy, XCircle, Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, type CoachResult, type DealDetail, type Extraction, type Memory } from "../lib/api";
import { fmtDate } from "../lib/format";
import { Markdown } from "../lib/markdown";
import { Chip, Drawer, Empty, Modal, Spinner, useToast } from "./ui";

// ------------------------------------------------------------------ Live coach

const EXAMPLES = [
  "Stratify is at ₹31L. Why should we pay ₹14L more?",
  "Honestly, this feels like a nice-to-have. Can we revisit next quarter?",
  "Our security team won't approve without SOC2 Type II.",
  "Can you just match Stratify's price?",
];

export function CoachDrawer({ deal, open, onClose, onChanged }: { deal: DealDetail; open: boolean; onClose: () => void; onChanged: () => void }) {
  const toast = useToast();
  const [objection, setObjection] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<CoachResult | null>(null);
  const [voted, setVoted] = useState<null | boolean>(null);

  useEffect(() => {
    if (!speaker && deal.stakeholders.length) {
      const s = deal.stakeholders.find((p) => p.role.toLowerCase().includes((deal.persona || "").toLowerCase())) ?? deal.stakeholders[0]!;
      setSpeaker(`${s.name} (${s.role})`);
    }
  }, [deal, speaker]);

  const ask = async (text = objection) => {
    if (!text.trim()) return;
    setObjection(text);
    setBusy(true);
    setRes(null);
    setVoted(null);
    try {
      setRes(await api.coach(deal.id, text, speaker));
      onChanged();
    } catch (e) {
      toast({ title: "Coach failed", body: String(e), tone: "bad" });
    } finally {
      setBusy(false);
    }
  };

  const vote = async (worked: boolean) => {
    if (!res) return;
    setVoted(worked);
    try {
      const r = await api.outcome(res.suggestion_id, worked);
      const t = r.stats.tactics.find((x) => x.tactic === res.response.tactic_name);
      toast({
        title: worked ? "Playbook learned a win" : "Playbook learned what not to do",
        body: t ? `“${t.tactic}” is now ${t.wins}W–${t.losses}L. Future briefs will use this.` : "Outcome retained to Hindsight.",
        tone: worked ? "good" : "warn",
      });
      onChanged();
    } catch (e) {
      toast({ title: "Could not record outcome", body: String(e), tone: "bad" });
      setVoted(null);
    }
  };

  const r = res?.response;
  return (
    <Drawer open={open} onClose={onClose} width="max-w-2xl" title={<span className="flex items-center gap-2"><Zap className="h-5 w-5 text-brand" />Live objection coach</span>}>
      <div className="space-y-4">
        <div className="card p-4">
          <div className="label mb-2">What did they just say?</div>
          <textarea
            autoFocus rows={3} className="input resize-none text-base" value={objection}
            onChange={(e) => setObjection(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask(); }}
            placeholder="Type or paste the objection…"
          />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <select className="input !w-auto !py-1.5 text-xs" value={speaker} onChange={(e) => setSpeaker(e.target.value)}>
              <option value="">Speaker: unknown</option>
              {deal.stakeholders.map((s) => <option key={s.id} value={`${s.name} (${s.role})`}>{s.name} · {s.role}</option>)}
            </select>
            <button className="btn-primary ml-auto" disabled={busy || !objection.trim()} onClick={() => ask()}>
              {busy ? <Spinner /> : <Send className="h-4 w-4" />} Coach me
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {EXAMPLES.map((e) => (
              <button key={e} onClick={() => ask(e)} disabled={busy} className="chip border-line bg-panel2 text-sub transition hover:border-brand/40 hover:text-ink">{e}</button>
            ))}
          </div>
        </div>

        {busy && (
          <div className="card space-y-3 p-5">
            <div className="flex items-center gap-2 text-sm text-sub"><Spinner className="text-brand" />Recalling this deal and what worked in past deals…</div>
            <div className="skeleton h-5 w-3/4" /><div className="skeleton h-5 w-full" /><div className="skeleton h-5 w-2/3" />
          </div>
        )}

        {r && !busy && (
          <div className="space-y-4 animate-rise">
            <div className="card overflow-hidden border-brand/35">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-brand/10 px-5 py-3">
                <div className="flex items-center gap-2 font-display font-semibold"><Quote className="h-4 w-4 text-brand" />{r.tactic_name || "Suggested response"}</div>
                <div className="flex items-center gap-1.5">
                  <Chip tone={r.confidence === "high" ? "good" : r.confidence === "medium" ? "warn" : "sub"}>{r.confidence} confidence</Chip>
                  <Chip><Timer className="h-3 w-3" />{(res!.latency_ms / 1000).toFixed(1)}s</Chip>
                </div>
              </div>
              <div className="space-y-4 p-5">
                <p className="text-[17px] leading-relaxed">“{r.response_script}”</p>
                {r.follow_up_question && (
                  <div className="rounded-xl border border-line bg-panel2/50 p-3 text-sm"><span className="label mr-2">Then ask</span>{r.follow_up_question}</div>
                )}
                {r.why_this_works && <p className="text-xs text-sub"><b className="text-ink">Why:</b> {r.why_this_works}</p>}
              </div>
            </div>

            {r.evidence.length > 0 && (
              <div>
                <div className="label mb-2 flex items-center gap-1.5"><BookOpen className="h-3.5 w-3.5" />Evidence from memory</div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {r.evidence.map((e, i) => {
                    const m = res!.citations[e.memory_id];
                    return (
                      <div key={i} className="rounded-xl border border-line bg-panel p-3 text-xs" title={m?.text}>
                        <div className="mb-1 flex items-center justify-between">
                          <span className="font-semibold">{e.deal || "This deal"}</span>
                          <Chip tone={e.outcome === "won" || e.outcome === "advanced" ? "good" : e.outcome === "lost" ? "bad" : "sub"}>{e.outcome}</Chip>
                        </div>
                        <div className="text-sub">{e.summary}</div>
                        <div className="mt-1.5 font-mono text-[9px] text-faint">{e.memory_id}{m?.date ? ` · ${fmtDate(m.date, true)}` : ""}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {r.avoid.length > 0 && (
              <div className="rounded-xl border border-bad/30 bg-bad/5 p-4">
                <div className="label mb-2 !text-bad">Avoid — this failed before</div>
                <ul className="space-y-1 text-sm">{r.avoid.map((a, i) => <li key={i} className="flex gap-2"><Ban className="mt-0.5 h-3.5 w-3.5 shrink-0 text-bad" />{a}</li>)}</ul>
              </div>
            )}

            <div className="card flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="text-sm"><b>Did it land?</b> <span className="text-sub">Your answer trains the team playbook.</span></div>
              <div className="flex gap-2">
                <button className={clsx("btn-ghost", voted === true && "!border-good !bg-good/15 !text-good")} disabled={voted !== null} onClick={() => vote(true)}><ThumbsUp className="h-4 w-4" />Worked</button>
                <button className={clsx("btn-ghost", voted === false && "!border-bad !bg-bad/15 !text-bad")} disabled={voted !== null} onClick={() => vote(false)}><ThumbsDown className="h-4 w-4" />Didn't work</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Drawer>
  );
}

// ------------------------------------------------------------------ Log interaction

export function LogInteractionModal({ deal, open, onClose, onDone }: { deal: DealDetail; open: boolean; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [f, setF] = useState({ type: "call", title: "", date: new Date().toISOString().slice(0, 16), content: "" });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ extraction: Extraction; memory_text: string } | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await api.addInteraction(deal.id, { ...f, date: new Date(f.date).toISOString(), participants: [] });
      setResult(r);
      onDone();
      toast({ title: "Retained to memory", body: `${r.extraction.objections.length} objections, ${r.extraction.commitments.length} commitments extracted.`, tone: "good" });
    } catch (err) {
      toast({ title: "Could not process interaction", body: String(err), tone: "bad" });
    } finally {
      setBusy(false);
    }
  };

  const close = () => { setResult(null); setF({ ...f, title: "", content: "" }); onClose(); };

  return (
    <Modal open={open} onClose={close} wide title={<span className="flex items-center gap-2"><Mic className="h-5 w-5 text-brand" />Log interaction · {deal.company}</span>}>
      {!result ? (
        <form onSubmit={submit} className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <label><div className="label mb-1">Type</div>
              <select className="input" value={f.type} onChange={(e) => setF({ ...f, type: e.target.value })}>
                <option value="call">Call transcript</option><option value="email">Email</option><option value="meeting">Meeting notes</option><option value="note">Rep note</option>
              </select></label>
            <label className="sm:col-span-2"><div className="label mb-1">Title</div>
              <input className="input" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} placeholder="e.g. Call 4 with CFO and Procurement" /></label>
          </div>
          <label className="block"><div className="label mb-1">When</div>
            <input type="datetime-local" className="input" value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} /></label>
          <label className="block"><div className="label mb-1">Transcript / email / notes</div>
            <textarea required rows={10} className="input font-mono text-xs leading-relaxed" value={f.content} onChange={(e) => setF({ ...f, content: e.target.value })}
              placeholder={"Priya Menon (CFO): We have Stratify at ₹31L…\nRahul (AE): …"} /></label>
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-sub">DealMind extracts objections, people, pricing and promises, then retains them to Hindsight.</span>
            <button className="btn-primary" disabled={busy}>{busy ? <Spinner /> : <Brain className="h-4 w-4" />}{busy ? "Extracting & remembering…" : "Process & remember"}</button>
          </div>
        </form>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-good"><CheckCircle2 className="h-4 w-4" />Extracted and retained to <span className="font-mono text-xs">deal bank</span></div>
          <p className="text-sm text-sub">{result.extraction.summary}</p>
          <div>
            <div className="label mb-1.5">What was written to memory</div>
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-xl border border-line bg-panel2/50 p-3 font-sans text-xs leading-relaxed">{result.memory_text}</pre>
          </div>
          <div className="flex justify-end"><button className="btn-primary" onClick={close}>Done</button></div>
        </div>
      )}
    </Modal>
  );
}

// ------------------------------------------------------------------ Close deal

export function CloseDealModal({ deal, open, onClose, onDone }: { deal: DealDetail; open: boolean; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [result, setResult] = useState<"won" | "lost">("won");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const submit = async () => {
    setBusy(true);
    try {
      const r = await api.close(deal.id, result, reason);
      setAnalysis(r.analysis);
      onDone();
    } catch (e) {
      toast({ title: "Could not close deal", body: String(e), tone: "bad" });
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal open={open} onClose={onClose} wide title={<span className="flex items-center gap-2"><Gavel className="h-5 w-5 text-brand" />Close {deal.company}</span>}>
      {!analysis ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            {(["won", "lost"] as const).map((r) => (
              <button key={r} onClick={() => setResult(r)} className={clsx("flex items-center justify-center gap-2 rounded-xl border p-4 font-semibold transition",
                result === r ? (r === "won" ? "border-good bg-good/10 text-good" : "border-bad bg-bad/10 text-bad") : "border-line text-sub hover:bg-panel2")}>
                {r === "won" ? <Trophy className="h-5 w-5" /> : <XCircle className="h-5 w-5" />} Closed {r}
              </button>
            ))}
          </div>
          <label className="block"><div className="label mb-1">In one line, why?</div>
            <input className="input" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. TCO + pilot beat Stratify on price" /></label>
          <p className="text-xs text-sub">DealMind will reflect over this deal's full memory and write a post-mortem into the team playbook.</p>
          <div className="flex justify-end"><button className="btn-primary" onClick={submit} disabled={busy}>{busy ? <Spinner /> : <Brain className="h-4 w-4" />}{busy ? "Reflecting on the deal…" : "Close & learn"}</button></div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-good"><CheckCircle2 className="h-4 w-4" />Post-mortem retained to the team playbook</div>
          <div className="rounded-xl border border-line bg-panel2/40 p-4 text-sm"><Markdown text={analysis} /></div>
          <div className="flex justify-end"><button className="btn-primary" onClick={onClose}>Done</button></div>
        </div>
      )}
    </Modal>
  );
}

// ------------------------------------------------------------------ Memory inspector

const typeTone: Record<string, "brand" | "info" | "good" | "warn" | "sub"> = {
  world: "info", experience: "good", observation: "brand", opinion: "warn",
};

export function MemoryInspector({ open, onClose, dealId, defaultQuery }: { open: boolean; onClose: () => void; dealId?: string; defaultQuery: string }) {
  const [q, setQ] = useState(defaultQuery);
  const [data, setData] = useState<{ bank: string; memories: Memory[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const run = async (query = q) => {
    setBusy(true);
    try {
      setData(dealId ? await api.dealMemories(dealId, query) : await api.playbookMemories(query));
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => { if (open) run(defaultQuery); }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Drawer open={open} onClose={onClose} title={<span className="flex items-center gap-2"><Database className="h-5 w-5 text-brand" />Memory inspector</span>}>
      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); run(); }}>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-faint" />
          <input className="input pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask the memory bank…" />
        </div>
        <button className="btn-primary" disabled={busy}>{busy ? <Spinner /> : "Recall"}</button>
      </form>
      {data && <div className="mt-2 font-mono text-[10px] text-faint">bank: {data.bank} · {data.memories.length} results</div>}
      <div className="mt-4 space-y-2">
        {busy && [0, 1, 2, 3].map((i) => <div key={i} className="skeleton h-16" />)}
        {!busy && data?.memories.length === 0 && <Empty icon={<Database className="h-5 w-5" />} title="Nothing recalled" hint="This bank has no memories matching that query yet." />}
        {!busy && data?.memories.map((m) => (
          <div key={m.id + m.label} className="animate-rise rounded-xl border border-line bg-panel p-3">
            <div className="mb-1 flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5">
                <Chip tone={typeTone[m.type] ?? "sub"}>{m.type}</Chip>
                {m.context && <Chip>{m.context}</Chip>}
              </div>
              <span className="text-[10px] text-faint">{fmtDate(m.date, true)}</span>
            </div>
            <div className="text-xs leading-relaxed">{m.text}</div>
          </div>
        ))}
      </div>
    </Drawer>
  );
}
