import clsx from "clsx";
import { BookOpenCheck, Brain, LayoutGrid, Moon, Sun } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { api, type Health } from "../lib/api";

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand to-brand2 shadow-glow">
        <Brain className="h-5 w-5 text-white" />
      </div>
      <div>
        <div className="font-display text-[17px] font-bold leading-none tracking-tight">DealMind</div>
        <div className="mt-1 text-[10px] font-medium uppercase tracking-[0.14em] text-faint">Deal intelligence</div>
      </div>
    </div>
  );
}

export function MemoryStatus() {
  const [h, setH] = useState<Health | null>(null);
  useEffect(() => {
    const load = () => api.health().then(setH).catch(() => setH(null));
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);
  const hindsight = h?.memory.backend === "hindsight";
  return (
    <div className="space-y-2 rounded-xl border border-line bg-panel2/60 p-3 text-xs">
      <div className="flex items-center gap-2">
        <span className={clsx("h-2 w-2 rounded-full animate-pulseDot", !h ? "bg-bad" : hindsight ? "bg-good" : "bg-warn")} />
        <span className="font-medium">{!h ? "Backend offline" : hindsight ? "Hindsight connected" : "Local memory (offline)"}</span>
      </div>
      {h && !hindsight && h.memory.degraded_reason && <div className="text-[11px] leading-snug text-warn">{h.memory.degraded_reason}</div>}
      {h && (
        <div className="flex items-center gap-2 text-sub">
          <span className={clsx("h-2 w-2 rounded-full", h.llm.configured ? "bg-good" : "bg-bad")} />
          <span className="truncate font-mono text-[10px]">{h.llm.configured ? h.llm.model : "GROQ_API_KEY missing"}</span>
        </div>
      )}
      {h && h.pending_retains > 0 && <div className="text-[11px] text-warn">{h.pending_retains} memories queued for retry</div>}
    </div>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem("dm-theme") || "dark";
    } catch {
      return "dark";
    }
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("dm-theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  const nav = [
    { to: "/", label: "Pipeline", icon: LayoutGrid },
    { to: "/playbook", label: "Playbook", icon: BookOpenCheck },
  ];

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-line bg-panel/60 p-4 backdrop-blur md:flex">
        <Logo />
        <nav className="mt-8 space-y-1">
          {nav.map((n) => (
            <NavLink
              key={n.to} to={n.to} end={n.to === "/"}
              className={({ isActive }) => clsx(
                "flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium transition",
                isActive ? "bg-brand/15 text-ink shadow-[inset_0_0_0_1px_rgb(var(--brand)/0.3)]" : "text-sub hover:bg-panel2 hover:text-ink",
              )}
            >
              <n.icon className="h-4 w-4" /> {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto space-y-3">
          <MemoryStatus />
          <div className="flex items-center justify-between px-1 text-xs text-sub">
            <span>Rahul Verma · AE</span>
            <button className="rounded-lg p-1.5 hover:bg-panel2" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Toggle theme">
              {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-line px-4 py-3 md:hidden">
          <Logo />
          <nav className="flex gap-1">
            {nav.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.to === "/"} className={({ isActive }) => clsx("rounded-lg p-2", isActive ? "bg-brand/15 text-brand" : "text-sub")}>
                <n.icon className="h-4 w-4" />
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 md:px-8 md:py-8">{children}</main>
      </div>
    </div>
  );
}
