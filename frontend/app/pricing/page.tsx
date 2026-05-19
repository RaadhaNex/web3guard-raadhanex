import { PricingSection } from "@/components/sections/PricingSection";

export default function PricingPage() {
  return (
    <>
      <section className="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8">
        <div className="quantum-stage p-6 sm:p-8">
          <p className="section-label">Pricing</p>
          <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">
            Free public beta now. Paid plans stay locked until payment verification is complete.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
            Web3Guard AI currently focuses on free launch-readiness scanning, direct report export, and evidence-first guidance. Razorpay, UPI, subscriptions, webhooks, and billing automation remain deferred until the final payment phase is verified end to end.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="badge badge-green">Free scanner live</span>
            <span className="badge badge-amber">Payments deferred</span>
            <span className="badge badge-cyan">No fake checkout success</span>
            <span className="badge">Pre-audit only</span>
          </div>
        </div>
      </section>
      <PricingSection />
    </>
  );
}
