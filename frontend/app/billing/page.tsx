import Link from "next/link";
import { StatusPill } from "@/components/ui/StatusPill";

const pendingItems = [
  "UPI QR / UTR submission flow",
  "Admin manual verification panel",
  "Razorpay test checkout + webhook verification",
  "Payment audit log review",
  "Subscription activation only after verified payment",
];

export default function BillingPage() {
  return (
    <main className="command-page">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <section className="command-hero p-6 sm:p-8">
          <div className="relative z-[1] max-w-4xl">
            <p className="section-label text-amber-200">Billing readiness</p>
            <h1 className="mt-3 text-4xl font-black sm:text-5xl">Payments stay deferred until real verification is complete.</h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
              Web3Guard AI keeps paid access honest: no frontend-only subscription state, no fake payment success, and no premium unlock until admin or provider verification exists.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="btn-primary">Run free scan</Link>
              <Link href="/pricing" className="btn-secondary">View planning prices</Link>
              <Link href="/feature-status" className="btn-secondary">Feature status</Link>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          <div className="command-card p-5">
            <StatusPill status="Live now" />
            <p className="mt-3 text-2xl font-black text-white">Free scan</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">URL scan, saved reports, and direct PDF/HTML/Markdown/JSON export.</p>
          </div>
          <div className="command-card p-5">
            <StatusPill status="Deferred" />
            <p className="mt-3 text-2xl font-black text-white">UPI manual</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">Will require reference submission and admin verification before access activation.</p>
          </div>
          <div className="command-card p-5">
            <StatusPill status="Provider pending" />
            <p className="mt-3 text-2xl font-black text-white">Razorpay</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">Enabled only after test checkout, signature verification, and webhook audit pass.</p>
          </div>
        </section>

        <section className="command-card mt-8 p-6 shadow-sm">
          <h2 className="text-2xl font-black text-white">Final payment-phase checklist</h2>
          <ul className="mt-5 grid gap-3 md:grid-cols-2">
            {pendingItems.map((item) => (
              <li key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm font-semibold text-slate-300">
                {item}
              </li>
            ))}
          </ul>
        </section>

        <section className="safe-copy mt-8 p-6 text-sm leading-6">
          <h2 className="text-xl font-black text-amber-100">Blocked until payment phase</h2>
          <p className="mt-2">
            Do not display “Paid”, “Subscription active”, “Payment successful”, or “Premium unlocked” unless payment is verified by admin or a real payment provider webhook/signature.
          </p>
        </section>
      </div>
    </main>
  );
}
