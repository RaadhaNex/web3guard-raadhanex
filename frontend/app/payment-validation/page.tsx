import Link from "next/link";
import { PaymentValidationClient } from "@/components/payment-validation/PaymentValidationClient";

export default function PaymentValidationPage() {
  return (
    <main className="command-page">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <section className="command-hero p-6 sm:p-8">
          <div className="relative z-[1] max-w-4xl">
            <p className="section-label">Phase 34</p>
            <h1 className="mt-3 text-4xl font-black sm:text-5xl">Payment validation + first paid flow sprint.</h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
              This page validates Razorpay test/live readiness, manual UPI fallback, paid access gates, and first ₹999 report flow without fake payment success or subscription unlocks.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/pricing" className="btn-primary">Open pricing</Link>
              <Link href="/results" className="btn-secondary">View scanner results</Link>
              <Link href="/billing" className="btn-secondary">Billing status</Link>
            </div>
            <p className="mt-4 text-xs text-slate-500">No frontend-only paid state · no fake payment success · no certified audit claim</p>
          </div>
        </section>

        <section className="mt-8">
          <PaymentValidationClient />
        </section>
      </div>
    </main>
  );
}
