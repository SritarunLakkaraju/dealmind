import clsx from "clsx";
import { ArrowUpRight, CalendarClock, MessagesSquare, Plus, Swords, Trophy, Users, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Chip, HealthRing, Modal, Spinner, useToast } from "../components/ui";
import { api, type Deal, type PlaybookStats } from "../lib/api";
import { fmtDate, inr, relative } from "../lib/format";

function Stat({ icon, label, value, hint }: { icon: React.ReactNode; label: string; value: string; hint?: string }) {
  return (
    <div className="card flex items-center gap-4 p-4">
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand/10 text-brand">{icon}</div>
      <div>
        <div className="label">{label}</div>
        <div className="font-display text-xl font-semibold">{value}</div>
        {hint && <div className="text-[11px] text-sub">{hint}</div>}
      </div>
    </div>
  );
}

function DealCard({ d, i }: { d: Deal; i: number }) {
  const closed = d.status !== "open";
  return (
    <Link
      to={`/deals/${d.id}`}
      style={{ animationDelay: `${i * 60}ms` }}
      className={clsx(
        "card group relative flex animate-rise flex-col gap-4 overflow-hidden p-5 transition hover:-translate-y-0.5 hover:border-brand/40",
        closed && "opacity-80 hover:opacity-100",
      )}
    >
      {!closed && <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-brand to-brand2" />}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-display text-lg font-semibold">{d.company}</h3>
            <ArrowUpRight className="h-4 w-4 text-faint opacity-0 transition group-hover:opacity-100" />
          </div>
          <div className="truncate text-xs text-sub">{d.name.split("—")[1]?.trim() || d.name}</div>
        </div>
        {closed ? (
          <Chip tone={d.status === "won" ? "good" : "bad"}>{d.status === "won" ? "Won" : "Lost"}</Chip>
        ) : (
          <HealthRing value={d.health} size={48} stroke={5} />
        )}
      </div>
      <div className="flex flex-wrap gap-1.5">
        <Chip tone="brand">{d.stage}</Chip>
        <Chip>{d.industry}</Chip>
        {d.primary_competitor && <Chip tone="warn"><Swords className="h-3 w-3" />{d.primary_competitor}</Chip>}
      </div>
      <div className="grid grid-cols-3 gap-3 border-t border-line pt-3 text-xs">
        <div>
          <div className="label !text-[10px]">ARR</div>
          <div className="mt-0.5 font-semibold">{inr(d.amount)}</div>
        </div>
        <div>
          <div className="label !text-[10px]">Touches</div>
          <div className="mt-0.5 flex items-center gap-1 font-semibold"><MessagesSquare className="h-3 w-3 text-faint" />{d.interaction_count}</div>
        </div>
        <div>
          <div className="label !text-[10px]">{closed ? "Closed" : "Next call"}</div>
          <div className={clsx("mt-0.5 font-semibold", !closed && d.next_meeting && "text-brand")}>
            {closed ? fmtDate(d.closed_at) : d.next_meeting ? relative(d.next_meeting) : "—"}
          </div>
        </div>
      </div>
    </Link>
  );
}

function NewDealModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const nav = useNavigate();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [f, setF] = useState({ company: "", industry: "", amount: "", primary_competitor: "", stage: "Discovery" });
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const d = await api.createDeal({
        company: f.company, name: `${f.company} — New opportunity`, industry: f.industry,
        amount: Number(f.amount) * 1e5 || 0, primary_competitor: f.primary_competitor, stage: f.stage,
      });
      nav(`/deals/${d.id}`);
    } catch (err) {
      toast({ title: "Could not create deal", body: String(err), tone: "bad" });
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal open={open} onClose={onClose} title="New deal">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
        <label className="sm:col-span-2"><div className="label mb-1">Company</div>
          <input required className="input" value={f.company} onChange={(e) => setF({ ...f, company: e.target.value })} placeholder="e.g. Saffron Retail" /></label>
        <label><div className="label mb-1">Industry</div>
          <input className="input" value={f.industry} onChange={(e) => setF({ ...f, industry: e.target.value })} placeholder="Retail" /></label>
        <label><div className="label mb-1">ARR (₹ lakh)</div>
          <input className="input" type="number" value={f.amount} onChange={(e) => setF({ ...f, amount: e.target.value })} placeholder="40" /></label>
        <label><div className="label mb-1">Competitor</div>
          <input className="input" value={f.primary_competitor} onChange={(e) => setF({ ...f, primary_competitor: e.target.value })} placeholder="Stratify" /></label>
        <label><div className="label mb-1">Stage</div>
          <select className="input" value={f.stage} onChange={(e) => setF({ ...f, stage: e.target.value })}>
            {["Discovery", "Evaluation", "Proposal", "Negotiation"].map((s) => <option key={s}>{s}</option>)}
          </select></label>
        <div className="flex justify-end gap-2 sm:col-span-2">
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={busy}>{busy && <Spinner />}Create deal</button>
        </div>
      </form>
    </Modal>
  );
}

export default function Pipeline() {
  const [deals, setDeals] = useState<Deal[] | null>(null);
  const [stats, setStats] = useState<PlaybookStats | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [newOpen, setNewOpen] = useState(false);

  useEffect(() => {
    api.deals().then(setDeals).catch((e) => setErr(String(e)));
    api.stats().then(setStats).catch(() => {});
  }, []);

  const open = deals?.filter((d) => d.status === "open") ?? [];
  const closed = deals?.filter((d) => d.status !== "open") ?? [];
  const won = closed.filter((d) => d.status === "won");

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="label">Good {new Date().getHours() < 12 ? "morning" : "afternoon"}, Rahul</div>
          <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">Your pipeline</h1>
          <p className="mt-1 max-w-xl text-sm text-sub">
            Every call, email and objection is remembered. Open a deal for a memory-powered brief before your next call.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setNewOpen(true)}><Plus className="h-4 w-4" />New deal</button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat icon={<Wallet className="h-5 w-5" />} label="Open pipeline" value={inr(open.reduce((s, d) => s + d.amount, 0))} hint={`${open.length} active deals`} />
        <Stat icon={<Trophy className="h-5 w-5" />} label="Closed won" value={inr(won.reduce((s, d) => s + d.amount, 0))} hint={`${won.length} of ${closed.length} closed`} />
        <Stat icon={<CalendarClock className="h-5 w-5" />} label="Next call" value={open.find((d) => d.next_meeting) ? relative(open.find((d) => d.next_meeting)!.next_meeting) : "—"} hint={open.find((d) => d.next_meeting)?.company} />
        <Stat icon={<Users className="h-5 w-5" />} label="Playbook lessons" value={String(stats?.total_outcomes ?? "—")} hint={stats ? `${stats.total_wins} winning tactics recorded` : undefined} />
      </div>

      {err && <div className="card border-bad/40 p-4 text-sm text-bad">Couldn't reach the backend: {err}</div>}

      <section>
        <div className="mb-3 flex items-center gap-2"><h2 className="font-display text-lg font-semibold">Active deals</h2><Chip tone="brand">{open.length}</Chip></div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {deals === null && [0, 1, 2].map((i) => <div key={i} className="skeleton h-48" />)}
          {open.map((d, i) => <DealCard key={d.id} d={d} i={i} />)}
        </div>
      </section>

      {closed.length > 0 && (
        <section>
          <div className="mb-1 flex items-center gap-2"><h2 className="font-display text-lg font-semibold">Closed deals</h2><Chip>{closed.length}</Chip></div>
          <p className="mb-3 text-xs text-sub">Their post-mortems train the shared playbook memory.</p>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {closed.map((d, i) => <DealCard key={d.id} d={d} i={i} />)}
          </div>
        </section>
      )}
      <NewDealModal open={newOpen} onClose={() => setNewOpen(false)} />
    </div>
  );
}
