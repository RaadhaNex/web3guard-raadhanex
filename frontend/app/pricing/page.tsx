import { PricingSection } from "@/components/sections/PricingSection";

export default function PricingPage() {
  return (
    <>
      <section className="mx-auto max-w-7xl px-4 pt-14 sm:px-6 lg:px-8">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Pricing + subscription</p>
        <h1 className="mt-3 text-4xl font-black sm:text-5xl">Razorpay + UPI paid reports and monthly subscriptions.</h1>
        <p className="mt-4 max-w-3xl text-slate-400">Users can pay through Razorpay Checkout when backend keys are configured, or use manual UPI fallback with admin verification. No frontend-only fake payment success is used.</p>
      </section>
      <PricingSection />
    </>
  );
}
