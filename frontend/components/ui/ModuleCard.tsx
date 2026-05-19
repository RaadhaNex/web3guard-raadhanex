import Link from "next/link";

export function ModuleCard({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <Link href={href} className="module-grid-card group block p-6">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan/25 bg-cyan/10 mono text-lg font-black text-cyan shadow-soft">
          W3
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1 text-[11px] font-black uppercase tracking-[0.16em] text-slate-400 transition group-hover:border-cyan/25 group-hover:text-cyan">
          Open
        </span>
      </div>
      <h3 className="text-lg font-black text-white">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
      <p className="mt-5 text-sm font-black text-cyan transition group-hover:translate-x-1">Continue →</p>
    </Link>
  );
}
