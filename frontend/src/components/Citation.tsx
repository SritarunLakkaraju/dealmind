import clsx from "clsx";
import { BookOpen, Brain, Sparkles, User } from "lucide-react";
import { useState } from "react";
import type { Memory } from "../lib/api";
import { fmtDate } from "../lib/format";

const kind = (label: string) => {
  const p = label[0];
  if (p === "P") return { name: "Playbook", icon: BookOpen, cls: "border-brand2/35 bg-brand2/10 text-brand2" };
  if (p === "R") return { name: "Reflection", icon: Sparkles, cls: "border-warn/35 bg-warn/10 text-warn" };
  if (p === "U") return { name: "Rep", icon: User, cls: "border-info/35 bg-info/10 text-info" };
  return { name: "Deal memory", icon: Brain, cls: "border-brand/35 bg-brand/10 text-brand" };
};

/** Citation chip — hover to see the exact Hindsight memory that backs a claim. */
export function Cite({ id, memory }: { id: string; memory?: Memory }) {
  const [open, setOpen] = useState(false);
  if (!memory) return null;
  const k = kind(id);
  const Icon = k.icon;
  return (
    <span className="relative inline-block align-middle" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={clsx("chip cursor-help font-mono !text-[10px] transition hover:brightness-125", k.cls)}
      >
        <Icon className="h-2.5 w-2.5" />
        {id}
        {memory.date && <span className="opacity-70">· {fmtDate(memory.date)}</span>}
      </button>
      {open && (
        <span className="absolute bottom-full left-0 z-30 mb-2 block w-80 animate-rise rounded-xl border border-line bg-panel p-3 text-left shadow-2xl">
          <span className="mb-1.5 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-faint">
            <span className="flex items-center gap-1"><Icon className="h-3 w-3" /> {k.name} · {memory.type}</span>
            <span>{fmtDate(memory.date, true)}</span>
          </span>
          <span className="block text-xs leading-relaxed text-ink">{memory.text}</span>
          <span className="mt-2 block truncate font-mono text-[9px] text-faint">{memory.bank}</span>
        </span>
      )}
    </span>
  );
}

export function Cites({ ids, citations }: { ids: string[]; citations: Record<string, Memory> }) {
  if (!ids?.length) return null;
  return (
    <span className="ml-1 inline-flex flex-wrap gap-1">
      {ids.slice(0, 4).map((id) => <Cite key={id} id={id} memory={citations[id]} />)}
    </span>
  );
}
