import Link from "next/link";
import { policies, trustPillars, whatWeCheck, whatWeDoNotClaim } from "@/lib/trustContent";

export function TrustBuilderSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">

      {/* Header */}
      <div className="grid gap-10 lg:grid-cols-[1fr_1.1fr]">
        <div>
          <p className="section-label">Security transparency</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">
            Honest about what we check and what we don&apos;t.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-7 text-slate-400">
            Web3Guard AI is a preliminary review platform — not a certified audit firm. We help early-stage builders find surface-level risks before committing to a full professional audit.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/trust" className="btn-primary">Trust Policy</Link>
            <Link href="/methodology" className="btn-secondary">Methodology</Link>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {trustPillars.map((item) => (
            <div key={item.title} className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5">
              <h3 className="text-sm font-bold text-white">{item.title}</h3>
              <p className="mt-2 text-xs leading-6 text-slate-400">{item.text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* What we check vs don't claim */}
      <div className="mt-10 grid gap-4 lg:grid-cols-2">
        <div className="card p-6">
          <div className="mb-4 flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-green-500/10 text-sm text-green-400">✓</span>
            <h3 className="text-lg font-black text-white">What we check</h3>
          </div>
          <ul className="space-y-2.5">
            {whatWeCheck.map((x) => (
              <li key={x} className="flex items-start gap-2 text-sm leading-5 text-slate-300">
                <span className="mt-0.5 shrink-0 text-green-400">✓</span>
                {x}
              </li>
            ))}
          </ul>
        </div>

        <div className="card p-6">
          <div className="mb-4 flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-500/10 text-sm text-red-400">✕</span>
            <h3 className="text-lg font-black text-white">What we do not claim</h3>
          </div>
          <ul className="space-y-2.5">
            {whatWeDoNotClaim.map((x) => (
              <li key={x} className="flex items-start gap-2 text-sm leading-5 text-slate-400">
                <span className="mt-0.5 shrink-0 text-red-400">✕</span>
                {x}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Policy links */}
      <div className="mt-6 grid gap-3 sm:grid-cols-2 md:grid-cols-4">
        {policies.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-4 transition hover:border-cyan/30 hover:bg-white/[0.04]"
          >
            <h3 className="text-sm font-bold text-white">{item.title}</h3>
            <p className="mt-1.5 text-xs leading-5 text-slate-400">{item.text}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
