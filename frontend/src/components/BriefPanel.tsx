import clsx from "clsx";
import {
  AlertOctagon, Ban, Brain, BrainCircuit, CheckCircle2, CircleDashed, HelpCircle, RefreshCw, ShieldAlert, Sparkles,
  Swords, UserRound,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { streamBrief, type BriefPayload } from "../lib/api";
import { fmtDateTime, stanceTone } from "../lib/format";
import { Cites } from "./Citation";
import { Chip, HealthRing, Spinner, healthTone } from "./ui";

type Step = { key: string; label: string; done: boolean };

function MemoryToggle({ on, onChange, disabled }: { on: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <div className="inline-flex rounded-xl border border-line bg-panel2 p-1 text-xs font-semibold">
      {[false, true].map((v) => (
        <button
          key={String(v)} disabled={disabled} onClick={() => onChange(v)}
          className={clsx(
            "flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition",
            on === v ? (v ? "bg-brand text-white shadow-glow" : "bg-panel text-ink shadow") : "text-sub hover:text-ink",
          )}
        >
          {v ? <BrainCircuit className="h-3.5 w-3.5" /> : <CircleDashed className="h-3.5 w-3.5" />}
          Memory {v ? "ON" : "OFF"}
        </button>
      ))}
    </div>
  );
}

function Block({ icon, title, children, tone }: { icon: React.ReactNode; title: string; children: React.ReactNode; tone?: string }) {
  return (
    <div className="animate-rise">
      <div className={clsx("mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em]", tone ?? "text-faint")}>
        {icon} {title}
      </div>
      {children}
    </div>
  );
}

export function BriefPanel({ dealId, initial, initialOff, onGenerated }: {
  dealId: string; initial: BriefPayload | null; initialOff: BriefPayload | null; onGenerated?: () => void;
}) {
  const [memoryOn, setMemoryOn] = useState(true);
  const [briefs, setBriefs] = useState<{ on: BriefPayload | null; off: BriefPayload | null }>({ on: initial, off: initialOff });
  const [steps, setSteps] = useState<Step[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const stop = useRef<() => void>();

  useEffect(() => () => stop.current?.(), []);
  useEffect(() => setBriefs({ on: initial, off: initialOff }), [dealId]); // eslint-disable-line react-hooks/exhaustive-deps

  const generate = (mem = memoryOn) => {
    stop.current?.();
    setRunning(true);
    setError(null);
    setSteps([]);
    stop.current = streamBrief(dealId, mem, (ev) => {
      if (ev.type === "step") {
        setSteps((s) => [...s.map((x) => ({ ...x, done: true })), { key: ev.key, label: ev.label, done: false }]);
      } else if (ev.type === "brief") {
        setSteps((s) => s.map((x) => ({ ...x, done: true })));
        setBriefs((b) => ({ ...b, [mem ? "on" : "off"]: ev }));
        setRunning(false);
        onGenerated?.();
      } else {
        setError(ev.message);
        setRunning(false);
      }
    });
  };

  const switchMemory = (v: boolean) => {
    setMemoryOn(v);
    if (!(v ? briefs.on : briefs.off) && !running) generate(v);
  };

  const payload = memoryOn ? briefs.on : briefs.off;
  const b = payload?.brief;
  const c = payload?.citations ?? {};

  return (
    <div className={clsx("card relative overflow-hidden transition", memoryOn && "border-brand/30")}>
      {memoryOn && <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-brand/10 blur-3xl" />}
      <div className="relative flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
        <div className="flex items-center gap-2.5">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-brand/15 text-brand"><Sparkles className="h-4 w-4" /></div>
          <div>
            <div className="font-display font-semibold">Pre-call brief</div>
            <div className="text-[11px] text-sub">
              {payload
                ? `Generated ${fmtDateTime(payload.generated_at)} · ${payload.stats.seconds}s${payload.memory ? ` · ${payload.stats.deal_memories} deal facts, ${payload.stats.playbook_memories} playbook lessons` : " · no memory"}`
                : "Not generated yet"}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <MemoryToggle on={memoryOn} onChange={switchMemory} disabled={running} />
          <button className="btn-ghost !px-2.5" onClick={() => generate()} disabled={running} title="Regenerate">
            {running ? <Spinner /> : <RefreshCw className="h-4 w-4" />}
          </button>
        </div>
      </div>

      <div className="relative p-5">
        {(running || (!payload && steps.length > 0)) && (
          <div className="mb-5 space-y-2 rounded-xl border border-line bg-panel2/50 p-4">
            {steps.map((s) => (
              <div key={s.key} className="flex items-center gap-2 text-sm">
                {s.done ? <CheckCircle2 className="h-4 w-4 text-good" /> : <Spinner className="text-brand" />}
                <span className={s.done ? "text-sub" : "text-ink"}>{s.label}</span>
              </div>
            ))}
            {steps.length === 0 && <div className="flex items-center gap-2 text-sm text-sub"><Spinner /> Connecting…</div>}
          </div>
        )}
        {error && <div className="mb-4 rounded-xl border border-bad/40 bg-bad/10 p-3 text-sm text-bad">{error}</div>}

        {!payload && !running && (
          <div className="flex flex-col items-center gap-3 py-12 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-brand/10 text-brand"><Brain className="h-7 w-7" /></div>
            <div className="font-display text-lg font-semibold">Brief me for the next call</div>
            <p className="max-w-sm text-sm text-sub">
              DealMind recalls every call, email and objection in this deal, checks what worked in past deals, and writes a 30-second brief.
            </p>
            <button className="btn-primary mt-2" onClick={() => generate()}><Sparkles className="h-4 w-4" />Generate brief</button>
          </div>
        )}

        {b && !running && (
          <div key={`${memoryOn}-${payload?.generated_at}`} className="space-y-6">
            {b.partial && <div className="rounded-xl border border-warn/40 bg-warn/10 p-3 text-xs text-warn">The model returned an incomplete answer. Try regenerating.</div>}
            <div className="flex items-start gap-4 animate-rise">
              <HealthRing value={b.deal_health} size={64} />
              <div className="min-w-0">
                <div className="text-[15px] font-semibold leading-snug">{b.headline}</div>
                <div className="mt-1 text-xs text-sub">
                  <Chip tone={healthTone(b.deal_health)} className="mr-1.5">Deal health</Chip>{b.health_reason}
                </div>
              </div>
            </div>

            {b.pattern_alert && (
              <div className="animate-rise rounded-xl border border-bad/40 bg-gradient-to-r from-bad/15 to-transparent p-4">
                <div className="mb-1 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-bad"><AlertOctagon className="h-4 w-4" /> Pattern alert · learned from past deals</div>
                <div className="text-sm leading-relaxed">{b.pattern_alert}<Cites ids={b.pattern_alert_ids} citations={c} /></div>
              </div>
            )}

            <div className="grid gap-6 lg:grid-cols-2">
              {b.key_risks.length > 0 && (
                <Block icon={<ShieldAlert className="h-3.5 w-3.5" />} title="Key risks" tone="text-bad">
                  <ul className="space-y-2">
                    {b.key_risks.map((r, i) => (
                      <li key={i} className="flex gap-2 text-sm leading-relaxed"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-bad" /><span>{r.risk}<Cites ids={r.evidence_ids} citations={c} /></span></li>
                    ))}
                  </ul>
                </Block>
              )}
              {b.open_commitments.length > 0 && (
                <Block icon={<CheckCircle2 className="h-3.5 w-3.5" />} title="Open commitments" tone="text-warn">
                  <ul className="space-y-2">
                    {b.open_commitments.map((o, i) => (
                      <li key={i} className={clsx("rounded-lg border p-2.5 text-sm", o.overdue ? "border-bad/40 bg-bad/5" : "border-line bg-panel2/40")}>
                        <div className="flex flex-wrap items-center gap-1.5">
                          <Chip tone={o.owner === "us" ? "brand" : "sub"}>{o.owner === "us" ? "We owe" : "They owe"}</Chip>
                          {o.overdue && <Chip tone="bad">Overdue</Chip>}
                          {o.due && <span className="text-[11px] text-faint">due {o.due}</span>}
                        </div>
                        <div className="mt-1">{o.what}<Cites ids={o.evidence_ids} citations={c} /></div>
                      </li>
                    ))}
                  </ul>
                </Block>
              )}
            </div>

            {b.likely_objections.length > 0 && (
              <Block icon={<Swords className="h-3.5 w-3.5" />} title="Likely objections & winning tactics" tone="text-brand">
                <div className="grid gap-3 md:grid-cols-2">
                  {b.likely_objections.map((o, i) => (
                    <div key={i} className="rounded-xl border border-line bg-panel2/40 p-3.5">
                      <div className="text-sm font-medium">“{o.objection}”</div>
                      <div className="mt-2 flex items-start gap-2 text-sm">
                        <span className="mt-0.5 text-good">→</span>
                        <span><span className="font-semibold text-good">{o.recommended_tactic}</span>
                          <span className="block text-xs text-sub">{o.why}</span></span>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-1">
                        <Chip tone={o.confidence === "high" ? "good" : o.confidence === "medium" ? "warn" : "sub"}>{o.confidence} confidence</Chip>
                        <Cites ids={o.evidence_ids} citations={c} />
                      </div>
                    </div>
                  ))}
                </div>
              </Block>
            )}

            {b.stakeholder_notes.length > 0 && (
              <Block icon={<UserRound className="h-3.5 w-3.5" />} title="Who's in the room">
                <div className="grid gap-2 sm:grid-cols-2">
                  {b.stakeholder_notes.map((s, i) => (
                    <div key={i} className="rounded-xl border border-line p-3 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <div className="font-semibold">{s.name} <span className="font-normal text-sub">· {s.role}</span></div>
                        <Chip tone={stanceTone[s.stance] ?? "sub"}>{s.stance}</Chip>
                      </div>
                      <div className="mt-1 text-xs leading-relaxed text-sub">{s.what_they_care_about}<Cites ids={s.evidence_ids} citations={c} /></div>
                    </div>
                  ))}
                </div>
              </Block>
            )}

            <div className="grid gap-6 lg:grid-cols-2">
              {b.questions_to_ask.length > 0 && (
                <Block icon={<HelpCircle className="h-3.5 w-3.5" />} title="Questions to ask">
                  <ol className="list-decimal space-y-1.5 pl-5 text-sm marker:text-faint">{b.questions_to_ask.map((q, i) => <li key={i}>{q}</li>)}</ol>
                </Block>
              )}
              {b.do_not.length > 0 && (
                <Block icon={<Ban className="h-3.5 w-3.5" />} title="Do not" tone="text-bad">
                  <ul className="space-y-1.5 text-sm">{b.do_not.map((q, i) => <li key={i} className="flex gap-2"><Ban className="mt-0.5 h-3.5 w-3.5 shrink-0 text-bad" />{q}</li>)}</ul>
                </Block>
              )}
            </div>

            {!payload?.memory && (
              <div className="rounded-xl border border-dashed border-line p-3 text-center text-xs text-sub">
                This is what a stateless LLM knows. Switch <b className="text-brand">Memory ON</b> to see the difference.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
