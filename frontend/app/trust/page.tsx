import Link from "next/link";
import { trustPillars, whatWeCheck, whatWeDoNotClaim } from "@/lib/trustContent";

const manualScope = [
  "Scanner-backed findings review and severity prioritization",
  "Founder/admin OpSec checklist review",
  "Website, dApp, API, wallet-flow readiness review within submitted scope",
  "Written recommendations and next-step package suggestion",
  "Manual pre-audit notes only when scope is agreed and paid workflow is enabled",
];

export default function TrustPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="section-label">Trust & scope</p>
      <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Honest security positioning by RAADHANEX.</h1>
      <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
        Web3Guard AI is a preliminary Web3 launch-readiness layer. It helps teams prepare before professional audits, contests, bug bounties, or mainnet launches.
      </p>

      <div className="mt-8 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-5 text-sm leading-6 text-amber-100">
        This is a preliminary security review tool. It does not replace a full manual audit, certified assessment, or production security guarantee.
      </div>

      <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        {trustPillars.map((item) => (
          <div key={item.title} className="glass-tile p-5">
            <h2 className="font-black text-white">{item.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{item.text}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        <div className="glass-tile p-6">
          <h2 className="text-2xl font-black">What we check</h2>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">{whatWeCheck.map((x) => <li key={x}>✓ {x}</li>)}</ul>
        </div>
        <div className="glass-tile p-6">
          <h2 className="text-2xl font-black">What we do not claim</h2>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">{whatWeDoNotClaim.map((x) => <li key={x}>✕ {x}</li>)}</ul>
        </div>
      </div>

      <div className="glass-tile mt-10 p-6">
        <h2 className="text-2xl font-black">Manual review scope clarity</h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Manual review is useful when scanner findings show launch risk, but it must be scoped clearly before any paid or expert workflow begins.
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {manualScope.map((item) => <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">{item}</div>)}
        </div>
      </div>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link href="/scope-refund" className="btn-primary">Scope policy</Link>
        <Link href="/responsible-use" className="btn-secondary">Responsible use</Link>
        <Link href="/contact" className="btn-secondary">Request scope review</Link>
      </div>
    </main>
  );
}
