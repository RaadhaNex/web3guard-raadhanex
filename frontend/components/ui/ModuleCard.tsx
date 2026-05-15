import Link from "next/link";

export function ModuleCard({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <Link href={href} className="card block p-6 transition hover:-translate-y-1 hover:border-cyan/40">
      <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan/30 bg-cyan/10 text-lg font-black text-cyan">✓</div>
      <h3 className="text-lg font-black text-white">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
    </Link>
  );
}
