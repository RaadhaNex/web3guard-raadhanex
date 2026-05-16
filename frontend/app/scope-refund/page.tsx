import Link from "next/link";
import { scopeRules } from "@/lib/trustContent";

const deliverables = [
  ["Free Scan", "Automated preliminary score and findings only. No manual verification."],
  ["Quick Risk Scan Report — ₹999", "Short paid report based on submitted scan material and manual prioritization."],
  ["Detailed Launch Readiness — ₹2,999", "Expanded report across selected modules with founder/developer action list."],
  ["Fix Suggestion Pack — ₹7,999", "Detailed safe fix direction and implementation notes. Code must still be reviewed before production."],
  ["Manual Pre-Audit Review — ₹14,999+", "Manual review of agreed project surface. Scope confirmed before work starts."],
  ["Full Launch Readiness — ₹29,999+", "Broad pre-launch review across contract, website, dApp, API, wallet, admin, and report delivery."],
];

export default function ScopeRefundPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Scope / Refund Policy</p>
      <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Clear paid-review boundaries before work starts.</h1>
      <p className="mt-4 max-w-3xl text-slate-400">
        adds a practical scope policy so RAADHANEX can sell reports honestly, verify UPI payments manually, and avoid fake audit guarantees.
      </p>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        {deliverables.map(([title, text]) => (
          <div key={title} className="card p-6">
            <h2 className="text-xl font-black">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </div>

      <div className="card mt-10 p-6">
        <h2 className="text-2xl font-black">Rules for payment, scope, and refunds</h2>
        <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
          {scopeRules.map((rule) => <li key={rule}>• {rule}</li>)}
        </ul>
      </div>

      <div className="mt-8 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100">
        UPI payment links are real deep links, but payment is manually verified by admin. The app must not show fake automatic success unless Razorpay/webhook verification is implemented later.
      </div>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link href="/pricing" className="btn-primary">See Packages</Link>
        <Link href="/contact" className="btn-secondary">Submit Project</Link>
      </div>
    </div>
  );
}
