import clsx from "clsx";
import { BookOpenCheck, Brain, Database, Send, Sparkles, ThumbsDown, ThumbsUp, Trophy, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MemoryInspector } from "../components/Actions";
import { Chip, Empty, SectionTitle, Spinner } from "../components/ui";
import { api, type Memory, type PlaybookStats } from "../lib/api";
import { fmtDate } from "../lib/format";
import { Markdown } from "../lib/markdown";

const QUESTIONS = [
  "What works against Stratify on price objections from a CFO?",
  "Why did we lose Meridian Payments?",
  "How should we handle a CISO's security review?",
  "What beats the 'enterprise-grade' objection?",
];

function WinBar({ wins, losses }: { wins: number; losses: number }) {
  const n = wins + losses || 1;
  return (
    <div className="flex h-2 w-28 overflow-hidden rounded-full bg-panel2">
      <div className="bg-good transition-all" style={{ width: `${(wins / n) * 100}%` }} />
      <div className="bg-bad transition-all" style={{ width: `${(losses / n) * 100}%` }} />
    </div>
  );
}

export default function Playbook() {
  const [stats, setStats] = useState<PlaybookStats | null>(null);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState<{ q: string; answer: string; based_on: Memory[] } | null>(null);
  const [memOpen, setMemOpen] = useState(false);

  useEffect(() => { api.stats().then(setStats); }, []);

  const ask = async (question = q) => {
    if (!question.trim()) return;
    setQ(question);
    setBusy(true);
    try {
      const r = await api.ask(question);
      setAnswer({ q: question, ...r });
    } catch (e) {
      setAnswer({ q: question, answer: `**Error:** ${e}`, based_on: [] });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="label">Shared memory · learns from every deal</div>
          <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">Team playbook</h1>
          <p className="mt-1 max-w-2xl text-sm text-sub">
            Every tactic the coach suggests, every 👍/👎 from reps, and every win/loss post-mortem is retained here.
            Briefs and live coaching recall it, so the whole team gets smarter with each deal.
          </p>
        </div>
        <button className="btn-ghost" onClick={() => setMemOpen(true)}><Database className="h-4 w-4" />Inspect memory</button>
      </div>

      <div className="card relative overflow-hidden p-6">
        <div className="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full bg-brand/10 blur-3xl" />
        <div className="relative">
          <div className="mb-3 flex items-center gap-2 font-display text-lg font-semibold"><Sparkles className="h-5 w-5 text-brand" />Ask the playbook</div>
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); ask(); }}>
            <input className="input !py-3 text-base" value={q} onChange={(e) => setQ(e.target.value)} placeholder="What works against Stratify on price?" />
            <button className="btn-primary !px-5" disabled={busy}>{busy ? <Spinner /> : <Send className="h-4 w-4" />}Ask</button>
          </form>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {QUESTIONS.map((x) => <button key={x} onClick={() => ask(x)} disabled={busy} className="chip border-line bg-panel2 text-sub transition hover:border-brand/40 hover:text-ink">{x}</button>)}
          </div>
          {busy && <div className="mt-5 space-y-2"><div className="flex items-center gap-2 text-sm text-sub"><Spinner className="text-brand" />Reflecting over recorded outcomes and post-mortems…</div><div className="skeleton h-4 w-2/3" /><div className="skeleton h-4 w-full" /><div className="skeleton h-4 w-1/2" /></div>}
          {answer && !busy && (
            <div className="mt-5 animate-rise rounded-xl border border-line bg-panel2/40 p-4">
              <div className="label mb-2">{answer.q}</div>
              <Markdown text={answer.answer} className="text-sm leading-relaxed" />
              {answer.based_on.length > 0 && (
                <details className="mt-3 text-xs text-sub">
                  <summary className="cursor-pointer font-medium text-brand">Based on {answer.based_on.length} memories</summary>
                  <ul className="mt-2 space-y-1.5">{answer.based_on.map((m) => <li key={m.id} className="rounded-lg border border-line p-2"><span className="text-faint">{fmtDate(m.date, true)} · {m.type}</span><br />{m.text}</li>)}</ul>
                </details>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="card p-5">
          <SectionTitle icon={<BookOpenCheck className="h-4 w-4" />} right={stats && <span className="text-[11px] text-faint">{stats.total_outcomes} outcomes · {stats.total_wins} wins</span>}>What works (tactic × objection)</SectionTitle>
          {!stats ? <div className="skeleton h-64" /> : stats.tactics.length === 0 ? <Empty icon={<Brain className="h-5 w-5" />} title="No outcomes yet" hint="Use the live coach and mark tactics as worked or not." /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="label border-b border-line"><tr><th className="py-2 pr-3 font-semibold">Tactic</th><th className="pr-3 font-semibold">Objection</th><th className="pr-3 font-semibold">Record</th><th className="pr-3 font-semibold">Confidence</th><th className="font-semibold">Deals</th></tr></thead>
                <tbody>
                  {stats.tactics.map((t) => (
                    <tr key={t.tactic + t.category} className="border-b border-line/60 last:border-0">
                      <td className="py-3 pr-3 font-medium">{t.tactic}</td>
                      <td className="pr-3"><Chip>{t.category}</Chip></td>
                      <td className="pr-3"><div className="flex items-center gap-2"><WinBar wins={t.wins} losses={t.losses} /><span className="whitespace-nowrap font-mono text-xs"><span className="text-good">{t.wins}W</span>–<span className="text-bad">{t.losses}L</span></span></div></td>
                      <td className="pr-3"><span className={clsx("font-mono text-xs font-semibold", t.win_rate >= 0.6 ? "text-good" : t.win_rate < 0.4 ? "text-bad" : "text-warn")}>{Math.round(t.win_rate * 100)}%</span></td>
                      <td className="text-xs text-sub">{t.deals.join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card p-5">
          <SectionTitle>Recent learning</SectionTitle>
          <ul className="space-y-2">
            {stats?.recent.map((r) => (
              <li key={r.id} className="flex gap-2.5 rounded-xl border border-line p-3 text-xs">
                {r.worked ? <ThumbsUp className="mt-0.5 h-4 w-4 shrink-0 text-good" /> : <ThumbsDown className="mt-0.5 h-4 w-4 shrink-0 text-bad" />}
                <div><div className="font-semibold">{r.tactic}</div><div className="text-sub">{r.deal_name} · {r.category} · {fmtDate(r.date)}</div></div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <section>
        <h2 className="mb-3 font-display text-lg font-semibold">Deal post-mortems</h2>
        <div className="grid gap-4 lg:grid-cols-3">
          {stats?.postmortems.map((p) => (
            <Link to={`/deals/${p.deal_id}`} key={p.deal_id} className="card block p-5 transition hover:border-brand/40">
              <div className="mb-2 flex items-center justify-between">
                <div className="font-display font-semibold">{p.company}</div>
                <Chip tone={p.result === "won" ? "good" : "bad"}>{p.result === "won" ? <Trophy className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}{p.result}</Chip>
              </div>
              <div className="line-clamp-[10] text-xs leading-relaxed text-sub"><Markdown text={p.text} /></div>
            </Link>
          ))}
        </div>
      </section>

      <MemoryInspector open={memOpen} onClose={() => setMemOpen(false)} defaultQuery="Which tactics worked or failed, and why?" />
    </div>
  );
}
