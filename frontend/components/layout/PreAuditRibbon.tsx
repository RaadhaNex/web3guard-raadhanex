import Link from "next/link";

export function PreAuditRibbon() {
  return (
    <div className="preaudit-ribbon" role="note" aria-label="Pre-audit disclaimer">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-2 px-4 py-2 text-center text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400 sm:px-6 lg:px-8">
        <span className="text-cyan">Public beta</span>
        <span className="text-slate-600">•</span>
        <span>Pre-audit readiness only</span>
        <span className="text-slate-600">•</span>
        <span>No certified audit claim</span>
        <span className="text-slate-600">•</span>
        <Link href="/limitations" className="text-cyan hover:text-cyan-200">Read limitations</Link>
      </div>
    </div>
  );
}
