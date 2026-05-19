import Link from "next/link";
import { policies, trustPillars, whatWeCheck, whatWeDoNotClaim } from "@/lib/trustContent";

export function TrustBuilderSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <p className="section-label">Trust builder</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Honest about what we check and what we don&apos;t.</h2>
          <p className="mt-4 max-w-md text-sm leading-7 text-slate-400">
            Web3Guard AI is a preliminary readiness platform. It helps founders prepare evidence, fix obvious risk patterns, and decide what needs manual audit review next.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/security" className="btn-primary">Trust Policy</Link>
            <Link href="/methodology" className="btn-secondary">Methodology</Link>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {trustPillars.map((item, index) => (
            <div key={item.title} className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5">
              <span className="mb-4 grid h-9 w-9 place-items-center rounded-[10px] border border-cyan/20 bg-cyan/[0.07] text-sm font-black text-cyan">0{index + 1}</span>
              <h3 className="text-sm font-black text-white">{item.title}</h3>
              <p className="mt-2 text-xs leading-6 text-slate-400">{item.text}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10 grid gap-4 lg:grid-cols-2">
        <div className="card p-6">
          <div className="mb-4 flex items-center gap-2.5">
            <span className="grid h-7 w-7 place-items-center rounded-lg border border-emerald-400/20 bg-emerald-400/10 text-sm text-emerald-300">✓</span>
            <h3 className="text-lg font-black text-white">What we check</h3>
          </div>
          <ul className="space-y-2.5">
            {whatWeCheck.map((x) => (
              <li key={x} className="flex items-start gap-2 text-sm leading-5 text-slate-300">
                <span className="mt-0.5 shrink-0 text-emerald-300">✓</span>
                {x}
              </li>
            ))}
          </ul>
        </div>

        <div className="card p-6">
          <div className="mb-4 flex items-center gap-2.5">
            <span className="grid h-7 w-7 place-items-center rounded-lg border border-red-400/20 bg-red-400/10 text-sm text-red-300">✕</span>
            <h3 className="text-lg font-black text-white">What we don&apos;t claim</h3>
          </div>
          <ul className="space-y-2.5">
            {whatWeDoNotClaim.map((x) => (
              <li key={x} className="flex items-start gap-2 text-sm leading-5 text-slate-400">
                <span className="mt-0.5 shrink-0 text-red-300">✕</span>
                {x}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 md:grid-cols-4">
        {policies.map((item) => (
          <Link key={item.href} href={item.href} className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-4 transition hover:-translate-y-0.5 hover:border-cyan/30 hover:bg-white/[0.04]">
            <h3 className="text-sm font-black text-white">{item.title}</h3>
            <p className="mt-1.5 text-xs leading-5 text-slate-400">{item.text}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
