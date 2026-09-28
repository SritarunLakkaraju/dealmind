import clsx from "clsx";
import { Loader2, X } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

export type Tone = "good" | "warn" | "bad" | "info" | "brand" | "sub";

const toneCls: Record<Tone, string> = {
  good: "border-good/30 bg-good/10 text-good",
  warn: "border-warn/30 bg-warn/10 text-warn",
  bad: "border-bad/30 bg-bad/10 text-bad",
  info: "border-info/30 bg-info/10 text-info",
  brand: "border-brand/30 bg-brand/10 text-brand",
  sub: "border-line bg-panel2 text-sub",
};

export function Chip({ tone = "sub", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return <span className={clsx("chip", toneCls[tone], className)}>{children}</span>;
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={clsx("h-4 w-4 animate-spin", className)} />;
}

export function healthTone(h?: number | null): Tone {
  if (h == null) return "sub";
  return h >= 70 ? "good" : h >= 45 ? "warn" : "bad";
}

export function HealthRing({ value, size = 56, stroke = 6 }: { value?: number | null; size?: number; stroke?: number }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const v = value ?? 0;
  const tone = healthTone(value);
  const color = { good: "rgb(var(--good))", warn: "rgb(var(--warn))", bad: "rgb(var(--bad))", sub: "rgb(var(--faint))" }[
    tone as "good" | "warn" | "bad" | "sub"
  ];
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgb(var(--line))" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={value == null ? c : c * (1 - v / 100)}
          style={{ transition: "stroke-dashoffset .8s ease" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center font-display text-sm font-semibold">
        {value == null ? "—" : v}
      </div>
    </div>
  );
}

export function Modal({ open, onClose, title, children, wide }: {
  open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; wide?: boolean;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/55 p-4 backdrop-blur-sm" onMouseDown={onClose}>
      <div
        className={clsx("card max-h-[90vh] w-full overflow-y-auto p-6 animate-rise", wide ? "max-w-3xl" : "max-w-xl")}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-lg font-semibold">{title}</h3>
          <button className="rounded-lg p-1 text-sub hover:bg-panel2" onClick={onClose} aria-label="Close"><X className="h-4 w-4" /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Drawer({ open, onClose, title, children, width = "max-w-xl" }: {
  open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; width?: string;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className={clsx("fixed inset-0 z-40 transition", open ? "pointer-events-auto" : "pointer-events-none")}>
      <div className={clsx("absolute inset-0 bg-black/50 backdrop-blur-[2px] transition-opacity", open ? "opacity-100" : "opacity-0")} onClick={onClose} />
      <aside
        className={clsx(
          "absolute right-0 top-0 flex h-full w-full flex-col border-l border-line bg-bg shadow-2xl transition-transform duration-300",
          width, open ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <div className="font-display text-lg font-semibold">{title}</div>
          <button className="rounded-lg p-1 text-sub hover:bg-panel2" onClick={onClose} aria-label="Close"><X className="h-4 w-4" /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">{open && children}</div>
      </aside>
    </div>
  );
}

export function SectionTitle({ icon, children, right }: { icon?: ReactNode; children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between gap-2">
      <div className="flex items-center gap-2 text-sm font-semibold text-ink">
        {icon && <span className="text-brand">{icon}</span>}
        {children}
      </div>
      {right}
    </div>
  );
}

export function Empty({ icon, title, hint }: { icon: ReactNode; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
      <div className="grid h-11 w-11 place-items-center rounded-2xl bg-panel2 text-faint">{icon}</div>
      <div className="text-sm font-medium">{title}</div>
      {hint && <div className="max-w-xs text-xs text-sub">{hint}</div>}
    </div>
  );
}

// ------------------------------------------------------------------ toasts

type Toast = { id: number; title: string; body?: string; tone: Tone };
const ToastCtx = createContext<(t: Omit<Toast, "id">) => void>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((t: Omit<Toast, "id">) => {
    const id = Date.now() + Math.random();
    setToasts((xs) => [...xs, { ...t, id }]);
    setTimeout(() => setToasts((xs) => xs.filter((x) => x.id !== id)), 5000);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="fixed bottom-5 right-5 z-[60] flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div key={t.id} className={clsx("card animate-rise border-l-4 p-3.5", {
            "border-l-good": t.tone === "good", "border-l-bad": t.tone === "bad", "border-l-warn": t.tone === "warn",
            "border-l-brand": t.tone === "brand" || t.tone === "info" || t.tone === "sub",
          })}>
            <div className="text-sm font-semibold">{t.title}</div>
            {t.body && <div className="mt-0.5 text-xs text-sub">{t.body}</div>}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
