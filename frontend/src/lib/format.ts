export function inr(amount?: number | null): string {
  if (!amount) return "—";
  if (amount >= 1e7) return `₹${+(amount / 1e7).toFixed(2)}Cr`;
  return `₹${+(amount / 1e5).toFixed(1)}L`;
}

export function fmtDate(value?: string | null, withYear = false): string {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(+d)) return value.slice(0, 10);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", ...(withYear ? { year: "numeric" } : {}) });
}

export function fmtDateTime(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  return d.toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
}

export function relative(value?: string | null): string {
  if (!value) return "—";
  const diff = (new Date(value).getTime() - Date.now()) / 86400000;
  const days = Math.round(diff);
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  if (days === -1) return "yesterday";
  return days > 0 ? `in ${days} days` : `${-days} days ago`;
}

export function isOverdue(due?: string | null): boolean {
  if (!due) return false;
  return new Date(due).getTime() < new Date(new Date().toDateString()).getTime();
}

export const stanceTone: Record<string, "good" | "info" | "sub" | "warn" | "bad"> = {
  champion: "good",
  supporter: "info",
  neutral: "sub",
  skeptic: "warn",
  blocker: "bad",
};

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join("");
}
