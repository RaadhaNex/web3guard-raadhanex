import type { Severity } from "@/lib/types";

const styles: Record<Severity, string> = {
  critical: "border-red-400/40 bg-red-500/15 text-red-200",
  high: "border-orange-400/40 bg-orange-500/15 text-orange-200",
  medium: "border-amber-400/40 bg-amber-500/15 text-amber-100",
  low: "border-blue-400/40 bg-blue-500/15 text-blue-100",
  info: "border-slate-400/40 bg-slate-500/15 text-slate-200",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${styles[severity]}`}>{severity}</span>;
}
