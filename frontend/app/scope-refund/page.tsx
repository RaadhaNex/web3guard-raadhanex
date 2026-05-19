import Link from "next/link";
import { scopeRules } from "@/lib/trustContent";

const deliverables = [
  ["Free Scan", "Automated preliminary readiness scan and exportable report. No manual verification."],
  ["Builder Review", "Planned scoped review workflow for teams that need triage after free scan results."],
  ["Pre-Audit Pack", "Planned evidence package preparation for teams approaching auditors, contests, or bounty programs."],
  ["Launch Readiness Review", "Planned broader review across website, dApp, API, wallet UX, GitHub, and admin OpSec evidence."],
  ["Fix Direction Pack", "Planned safe fix direction and implementation notes. Production code still requires engineering review."],
  ["Post-Launch Protection", "Planned monitoring and incident-readiness support once live provider integrations are configured."],
];

export default function ScopeRefundPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="section-label">Scope policy</p>
      <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Clear boundaries before any paid review goes live.</h1>
      <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
        The free scanner is live. Paid reviews, subscriptions, Razorpay, UPI, and automated billing remain deferred until the final payment phase is verified. This page documents scope expectations without implying active checkout.
      </p>

      <div className="mt-8 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-5 text-sm leading-6 text-amber-100">
        Current status: payments are pending. Do not show fake success, paid access, subscription status, or automatic verification until the backend order, checkout, webhook, and audit log flow is live.
      </div>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        {deliverables.map(([title, text]) => (
          <div key={title} className="glass-tile p-6">
            <h2 className="text-xl font-black text-white">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </div>

      <div className="glass-tile mt-10 p-6">
        <h2 className="text-2xl font-black">Scope, payment, and refund rules</h2>
        <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
          {scopeRules.map((rule) => <li key={rule}>• {rule}</li>)}
        </ul>
      </div>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link href="/pricing" className="btn-primary">View pricing status</Link>
        <Link href="/contact" className="btn-secondary">Submit scope request</Link>
      </div>
    </main>
  );
}
