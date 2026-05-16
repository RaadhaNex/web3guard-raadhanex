import Link from "next/link";
import { trustPillars, whatWeCheck, whatWeDoNotClaim } from "@/lib/trustContent";

const manualScope = [
  "Scanner-backed findings review and severity prioritization",
  "Founder/admin OpSec checklist review",
  "Website/dApp/API/wallet-flow readiness review within submitted scope",
  "Written recommendations and next-step package suggestion",
  "Manual pre-audit notes where paid package allows it",
];

export default function TrustPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Trust & scope</p>
      <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Honest security positioning by RAADHANEX.</h1>
      <p className="mt-4 max-w-3xl text-slate-400">
        Web3Guard AI is built as a preliminary Web3 launch security review layer. It helps projects prepare before professional audits, paid contests, bug bounties, or mainnet launches.
      </p>

      <div className="mt-8 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-5 text-sm leading-6 text-amber-100">
        This is a preliminary security review and does not replace a full manual audit. We do not claim certified audit coverage, 100% security, or exploit-prevention guarantees.
      </div>

      <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        {trustPillars.map((item) => (
          <div key={item.title} className="card p-5">
            <h2 className="font-black">{item.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{item.text}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        <div className="card p-6">
          <h2 className="text-2xl font-black">What we check</h2>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">{whatWeCheck.map((x) => <li key={x}>✓ {x}</li>)}</ul>
        </div>
        <div className="card p-6">
          <h2 className="text-2xl font-black">What we do not claim</h2>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">{whatWeDoNotClaim.map((x) => <li key={x}>✕ {x}</li>)}</ul>
        </div>
      </div>

      <div className="card mt-10 p-6">
        <h2 className="text-2xl font-black">Manual review scope clarity</h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">Paid review is useful when scanner findings show launch risk, but it still needs clear scope. adds this clarity to avoid overpromising.</p>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {manualScope.map((item) => <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">{item}</div>)}
        </div>
      </div>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link href="/scope-refund" className="btn-primary">Scope / Refund Policy</Link>
        <Link href="/responsible-use" className="btn-secondary">Responsible Use</Link>
        <Link href="/contact" className="btn-secondary">Request Paid Review</Link>
      </div>
    </div>
  );
}
