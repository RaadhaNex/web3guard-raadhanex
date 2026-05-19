import Link from "next/link";
import { PricingSection } from "@/components/sections/PricingSection";

export default function PricingPage() {
  return (
    <main className="cinematic-page-shell">
      <section className="cinematic-page-hero mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8">
        <div className="clean-panel cinematic-panel p-6 sm:p-8">
          <p className="section-label">Pricing</p>
          <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
            Free scan first. ₹999 pilot report only after payment validation.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
            Web3Guard stays honest: free readiness scan is the public beta entry point. Paid pilot report flow should be used only when Razorpay/UPI validation is configured and payment status is verified by backend.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="badge badge-green">Free scanner live</span>
            <span className="badge badge-cyan">₹999 pilot report path</span>
            <span className="badge badge-amber">Verify payment before access</span>
            <span className="badge">Pre-audit only</span>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Run free scan →</Link>
            <Link href="/payment-validation" className="btn-secondary">Payment validation</Link>
            <Link href="/report" className="btn-secondary">Report flow</Link>
          </div>
        </div>
      </section>
      <PricingSection />
    </main>
  );
}
