import { ArrowLeft, CalendarClock, Database, Gavel, Mic, Swords, Trophy, XCircle, Zap } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CloseDealModal, CoachDrawer, LogInteractionModal, MemoryInspector } from "../components/Actions";
import { BriefPanel } from "../components/BriefPanel";
import { Commitments, StakeholderMap, Timeline } from "../components/DealWidgets";
import { Chip, useToast } from "../components/ui";
import { api, type DealDetail } from "../lib/api";
import { fmtDate, fmtDateTime, inr, relative } from "../lib/format";
import { Markdown } from "../lib/markdown";

export default function DealRoom() {
  const { id = "" } = useParams();
  const toast = useToast();
  const [deal, setDeal] = useState<DealDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [coachOpen, setCoachOpen] = useState(false);
  const [logOpen, setLogOpen] = useState(false);
  const [closeOpen, setCloseOpen] = useState(false);
  const [memOpen, setMemOpen] = useState(false);

  const load = useCallback(() => api.deal(id).then(setDeal).catch((e) => setErr(String(e))), [id]);
  useEffect(() => { setDeal(null); load(); }, [load]);

  const toggle = async (cid: number) => {
    try {
      await api.toggleCommitment(id, cid);
      load();
    } catch (e) {
      toast({ title: "Update failed", body: String(e), tone: "bad" });
    }
  };

  if (err) return <div className="card p-6 text-bad">{err}</div>;
  if (!deal) return (
    <div className="space-y-4"><div className="skeleton h-24" /><div className="grid gap-4 lg:grid-cols-3"><div className="skeleton h-[520px] lg:col-span-2" /><div className="skeleton h-[520px]" /></div></div>
  );

  const open = deal.status === "open";

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-sub hover:text-ink"><ArrowLeft className="h-3.5 w-3.5" />Pipeline</Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-display text-3xl font-bold tracking-tight">{deal.company}</h1>
            {open ? <Chip tone="brand">{deal.stage}</Chip> : <Chip tone={deal.status === "won" ? "good" : "bad"}>{deal.status === "won" ? <Trophy className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}Closed {deal.status}</Chip>}
          </div>
          <p className="mt-1 text-sm text-sub">{deal.description}</p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <Chip>{inr(deal.amount)} ARR</Chip>
            <Chip>{deal.industry}</Chip>
            {deal.primary_competitor && <Chip tone="warn"><Swords className="h-3 w-3" />vs {deal.primary_competitor}</Chip>}
            {open && deal.next_meeting && <Chip tone="info"><CalendarClock className="h-3 w-3" />Next call {fmtDateTime(deal.next_meeting)} · {relative(deal.next_meeting)}</Chip>}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn-ghost" onClick={() => setMemOpen(true)}><Database className="h-4 w-4" />Memory</button>
          <button className="btn-ghost" onClick={() => setLogOpen(true)}><Mic className="h-4 w-4" />Log interaction</button>
          {open && <button className="btn-ghost" onClick={() => setCloseOpen(true)}><Gavel className="h-4 w-4" />Close deal</button>}
          {open && <button className="btn-primary" onClick={() => setCoachOpen(true)}><Zap className="h-4 w-4" />Live coach</button>}
        </div>
      </div>

      {deal.postmortem && (
        <div className="card p-5">
          <div className="label mb-2">Post-mortem · {fmtDate(deal.postmortem.created_at, true)} · retained to team playbook</div>
          <div className="text-sm text-sub"><Markdown text={deal.postmortem.text} /></div>
          {deal.close_reason && <div className="mt-3 text-xs text-faint">Rep's reason: {deal.close_reason}</div>}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="min-w-0 space-y-6">
          <BriefPanel dealId={deal.id} initial={deal.brief} initialOff={deal.brief_off} />
          <Timeline items={deal.interactions} />
        </div>
        <div className="space-y-6">
          <StakeholderMap company={deal.company} people={deal.stakeholders} />
          <Commitments items={deal.commitments} onToggle={toggle} />
          {deal.suggestions.length > 0 && (
            <div className="card p-5">
              <div className="mb-3 text-sm font-semibold">Coaching history</div>
              <ul className="space-y-2">
                {deal.suggestions.map((s) => (
                  <li key={s.id} className="rounded-xl border border-line p-3 text-xs">
                    <div className="text-sub">“{s.objection}”</div>
                    <div className="mt-1 flex items-center justify-between gap-2">
                      <span className="font-semibold">{s.tactic}</span>
                      {s.outcome ? <Chip tone={s.outcome === "worked" ? "good" : "bad"}>{s.outcome}</Chip> : <Chip>pending</Chip>}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <CoachDrawer deal={deal} open={coachOpen} onClose={() => setCoachOpen(false)} onChanged={load} />
      <LogInteractionModal deal={deal} open={logOpen} onClose={() => setLogOpen(false)} onDone={load} />
      <CloseDealModal deal={deal} open={closeOpen} onClose={() => setCloseOpen(false)} onDone={load} />
      <MemoryInspector open={memOpen} onClose={() => setMemOpen(false)} dealId={deal.id}
        defaultQuery="Objections, pricing, competitors and promises in this deal" />
    </div>
  );
}
