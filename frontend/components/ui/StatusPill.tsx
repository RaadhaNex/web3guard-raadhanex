export function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const klass = normalized.includes("live") || normalized.includes("configured") || normalized.includes("verified") || normalized.includes("active")
    ? "border-emerald-300/30 bg-emerald-400/10 text-emerald-100"
    : normalized.includes("manual") || normalized.includes("limited") || normalized.includes("needs") || normalized.includes("pending") || normalized.includes("deferred")
      ? "border-amber-300/30 bg-amber-400/10 text-amber-100"
      : normalized.includes("not") || normalized.includes("disabled") || normalized.includes("off")
        ? "border-slate-400/30 bg-slate-400/10 text-slate-200"
        : "border-cyan/30 bg-cyan/10 text-cyan";

  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-black uppercase tracking-[0.14em] ${klass}`}>
      {status}
    </span>
  );
}
