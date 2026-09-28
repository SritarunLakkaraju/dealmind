import clsx from "clsx";
import { Check, ChevronDown, Clock, FileText, Mail, Mic, NotebookPen, Users } from "lucide-react";
import { useState } from "react";
import type { Commitment, Interaction, Stakeholder } from "../lib/api";
import { fmtDate, initials, isOverdue, stanceTone } from "../lib/format";
import { Chip, Empty, SectionTitle } from "./ui";

const stanceColor: Record<string, string> = {
  champion: "rgb(var(--good))", supporter: "rgb(var(--info))", neutral: "rgb(var(--faint))",
  skeptic: "rgb(var(--warn))", blocker: "rgb(var(--bad))",
};

export function StakeholderMap({ company, people }: { company: string; people: Stakeholder[] }) {
  const [active, setActive] = useState<Stakeholder | null>(null);
  const W = 100, H = 100, cx = 50, cy = 52;
  const n = Math.max(people.length, 1);
  const nodes = people.map((p, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / n;
    return { p, x: cx + 36 * Math.cos(a), y: cy + 36 * Math.sin(a) };
  });
  return (
    <div className="card p-5">
      <SectionTitle icon={<Users className="h-4 w-4" />} right={<span className="text-[11px] text-faint">from memory</span>}>Buying committee</SectionTitle>
      {people.length === 0 ? (
        <Empty icon={<Users className="h-5 w-5" />} title="No stakeholders yet" hint="Log a call and DealMind will map the buying committee." />
      ) : (
        <>
          <div className="relative mx-auto aspect-square w-full max-w-[320px]">
            <svg viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 h-full w-full">
              {nodes.map(({ p, x, y }) => (
                <line key={p.id} x1={cx} y1={cy} x2={x} y2={y} stroke={stanceColor[p.stance] ?? stanceColor.neutral}
                  strokeWidth={active?.id === p.id ? 0.9 : 0.5} strokeDasharray={p.stance === "neutral" ? "1.5 1.5" : undefined} opacity={0.7} />
              ))}
            </svg>
            <div className="absolute grid h-16 w-16 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-2xl border border-brand/50 bg-panel px-1 text-center text-[10px] font-semibold leading-tight shadow-glow"
              style={{ left: `${cx}%`, top: `${cy}%` }}>{company}</div>
            {nodes.map(({ p, x, y }) => (
              <button
                key={p.id} onMouseEnter={() => setActive(p)} onFocus={() => setActive(p)} onClick={() => setActive(p)}
                className="group absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
                style={{ left: `${x}%`, top: `${y}%` }}
              >
                <span className="grid h-11 w-11 place-items-center rounded-full border-2 bg-panel text-xs font-bold transition group-hover:scale-110"
                  style={{ borderColor: stanceColor[p.stance] ?? stanceColor.neutral }}>{initials(p.name)}</span>
                <span className="mt-1 whitespace-nowrap rounded bg-panel px-1 text-[10px] font-medium">{p.name.split(" ")[0]}</span>
                <span className="whitespace-nowrap rounded bg-panel px-1 text-[9px] text-faint">{p.role}</span>
              </button>
            ))}
          </div>
          <div className="mt-3 min-h-[64px] rounded-xl border border-line bg-panel2/40 p-3 text-xs">
            {active ? (
              <>
                <div className="flex items-center justify-between"><b>{active.name} · <span className="font-normal text-sub">{active.role}</span></b><Chip tone={stanceTone[active.stance] ?? "sub"}>{active.stance}</Chip></div>
                {active.concerns.length > 0 ? (
                  <ul className="mt-1.5 list-disc space-y-0.5 pl-4 text-sub">{active.concerns.slice(-3).map((c, i) => <li key={i}>{c}</li>)}</ul>
                ) : <div className="mt-1 text-sub">No concerns recorded yet.</div>}
              </>
            ) : <div className="text-faint">Hover a person to see what they care about.</div>}
          </div>
          <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-sub">
            {Object.entries(stanceColor).map(([k, v]) => (
              <span key={k} className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: v }} />{k}</span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export function Commitments({ items, onToggle }: { items: Commitment[]; onToggle: (id: number) => void }) {
  const sorted = [...items].sort((a, b) => a.done - b.done || (a.due_date ?? "9").localeCompare(b.due_date ?? "9"));
  return (
    <div className="card p-5">
      <SectionTitle icon={<Clock className="h-4 w-4" />} right={<span className="text-[11px] text-faint">{items.filter((i) => !i.done).length} open</span>}>Commitments</SectionTitle>
      {items.length === 0 ? <Empty icon={<Clock className="h-5 w-5" />} title="No promises tracked yet" /> : (
        <ul className="space-y-2">
          {sorted.map((c) => {
            const overdue = !c.done && isOverdue(c.due_date);
            return (
              <li key={c.id} className={clsx("flex items-start gap-3 rounded-xl border p-3 text-sm transition",
                c.done ? "border-line opacity-55" : overdue ? "border-bad/40 bg-bad/5" : "border-line")}>
                <button onClick={() => onToggle(c.id)} aria-label="Toggle done"
                  className={clsx("mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded border transition",
                    c.done ? "border-good bg-good text-white" : "border-faint hover:border-brand")}>
                  {c.done ? <Check className="h-3 w-3" /> : null}
                </button>
                <div className="min-w-0">
                  <div className={clsx(c.done && "line-through")}>{c.what}</div>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-faint">
                    <Chip tone={c.owner === "us" ? "brand" : "sub"}>{c.owner === "us" ? "We owe" : "They owe"}</Chip>
                    <span>{c.who}</span>
                    {c.due_date && <span className={clsx(overdue && "font-semibold text-bad")}>· due {fmtDate(c.due_date)}{overdue && " · OVERDUE"}</span>}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

const typeIcon = { call: Mic, email: Mail, meeting: Users, note: NotebookPen } as const;

function Signals({ it }: { it: Interaction }) {
  const ex = it.extraction;
  if (!ex) return <div className="text-xs text-faint">Not processed yet.</div>;
  return (
    <div className="space-y-3 text-xs">
      <p className="leading-relaxed text-sub">{ex.summary}</p>
      <div className="flex flex-wrap gap-1.5">
        {ex.objections.map((o, i) => <Chip key={`o${i}`} tone={o.resolved ? "sub" : "bad"} className="max-w-full"><span className="truncate">{o.category}: {o.text}</span></Chip>)}
        {ex.competitors.map((o, i) => <Chip key={`c${i}`} tone="warn">vs {o.name}</Chip>)}
        {ex.pricing.map((p, i) => p.amount ? <Chip key={`p${i}`} tone="info">₹{(p.amount / 1e5).toFixed(1)}L · {p.note}</Chip> : null)}
        {ex.commitments.map((c, i) => <Chip key={`m${i}`} tone="brand">{c.owner === "us" ? "We" : "They"}: {c.what}</Chip>)}
      </div>
    </div>
  );
}

export function Timeline({ items }: { items: Interaction[] }) {
  const [open, setOpen] = useState<string | null>(null);
  const [raw, setRaw] = useState<string | null>(null);
  return (
    <div className="card p-5">
      <SectionTitle icon={<FileText className="h-4 w-4" />} right={<span className="text-[11px] text-faint">{items.length} touches</span>}>Deal timeline</SectionTitle>
      {items.length === 0 ? <Empty icon={<FileText className="h-5 w-5" />} title="No interactions yet" hint="Log your first call or email." /> : (
        <ol className="relative space-y-1 before:absolute before:bottom-3 before:left-[15px] before:top-3 before:w-px before:bg-line">
          {items.map((it) => {
            const Icon = typeIcon[it.type] ?? FileText;
            const isOpen = open === it.id;
            return (
              <li key={it.id} className="relative">
                <button onClick={() => setOpen(isOpen ? null : it.id)} className="flex w-full items-start gap-3 rounded-xl p-2 text-left transition hover:bg-panel2/60">
                  <span className="relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full border border-line bg-panel text-brand"><Icon className="h-3.5 w-3.5" /></span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-medium">{it.title}</span>
                      <ChevronDown className={clsx("h-4 w-4 shrink-0 text-faint transition", isOpen && "rotate-180")} />
                    </span>
                    <span className="flex items-center gap-2 text-[11px] text-faint">
                      {fmtDate(it.date, true)} · {it.type}
                      {it.retained ? <span className="text-good">· in memory</span> : <span className="text-warn">· not retained</span>}
                    </span>
                  </span>
                </button>
                {isOpen && (
                  <div className="ml-11 mb-2 animate-rise space-y-2 rounded-xl border border-line bg-panel2/40 p-3">
                    <Signals it={it} />
                    <button className="text-[11px] font-medium text-brand hover:underline" onClick={() => setRaw(raw === it.id ? null : it.id)}>
                      {raw === it.id ? "Hide" : "Show"} original {it.type}
                    </button>
                    {raw === it.id && <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-bg/60 p-3 font-sans text-xs leading-relaxed text-sub">{it.content}</pre>}
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
