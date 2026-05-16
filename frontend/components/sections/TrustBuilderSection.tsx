import Link from "next/link";
import { policies, trustPillars, whatWeCheck, whatWeDoNotClaim } from "@/lib/trustContent";

export function TrustBuilderSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Trust builder</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Honest security copy that founders can actually use.</h2>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            turns Web3Guard AI into a trust-ready pre-audit platform: scope boundaries, methodology, sample reports, responsible-use policy, and paid-review clarity.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/trust" className="btn-primary">Read Trust Policy</Link>
            <Link href="/sample-reports" className="btn-secondary">View Sample Reports</Link>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {trustPillars.map((item) => (
            <div key={item.title} className="card p-5">
              <h3 className="font-black">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-400">{item.text}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="text-2xl font-black">What Web3Guard AI checks</h3>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
            {whatWeCheck.map((x) => <li key={x}>✓ {x}</li>)}
          </ul>
        </div>
        <div className="card p-6">
          <h3 className="text-2xl font-black">What we do not claim</h3>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
            {whatWeDoNotClaim.map((x) => <li key={x}>✕ {x}</li>)}
          </ul>
        </div>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-4">
        {policies.map((item) => (
          <Link key={item.href} href={item.href} className="card block p-5 transition hover:border-cyan/50">
            <h3 className="font-black">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">{item.text}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
