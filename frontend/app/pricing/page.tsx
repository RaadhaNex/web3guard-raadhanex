import Link from "next/link";
import { PricingSection } from "@/components/sections/PricingSection";

export default function PricingPage() {
  return (
    <>
      <section className="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8">
        <div className="quantum-stage p-6 sm:p-8">
          <p className="section-label">Pricing</p>
          <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">
            Free scans stay live. Paid plans unlock only after verified payment.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
            Phase 14 adds the real payment workflow: backend Razorpay order creation, Checkout signature verification, signed webhook processing, manual UPI fallback, audit logs, and plan-limit visibility. If provider keys are missing, the UI shows setup required instead of fake success.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="badge badge-green">Free scanner live</span>
            <span className="badge badge-cyan">Razorpay when configured</span>
            <span className="badge badge-amber">UPI manual fallback</span>
            <span className="badge">Pre-audit only</span>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/payment-validation" className="btn-secondary">Payment validation</Link>
            <Link href="/billing" className="btn-secondary">Billing readiness</Link>
            <Link href="/scanner/unified-url" className="btn-primary">Run free scan</Link>
            <Link href="/pilot-experience" className="btn-secondary">Pilot UX checklist</Link>
          </div>
        </div>
      </section>
      <PricingSection />
    </>
  );
}
