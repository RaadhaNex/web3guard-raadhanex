import { Hero } from "@/components/sections/Hero";
import { LaunchSurface } from "@/components/sections/LaunchSurface";
import { PricingSection } from "@/components/sections/PricingSection";
import { TrustStrip } from "@/components/sections/TrustStrip";
import { TrustBuilderSection } from "@/components/sections/TrustBuilderSection";
import { ProductionReadiness } from "@/components/sections/ProductionReadiness";
import { SampleScannerDemo } from "@/components/sections/SampleScannerDemo";

function HowItWorks() {
  const steps = [
    { n: "01", title: "Scan",      text: "Paste your contract, enter your URL, or fill the launch checklists. Free — no account needed to start." },
    { n: "02", title: "Review",    text: "Get a security score, severity breakdown, business impact, and specific fix directions for each finding." },
    { n: "03", title: "Act",       text: "Fix issues using our guidance, or request a paid manual expert review via UPI or Razorpay." },
  ];
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mb-10 text-center">
        <p className="section-label">How it works</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Three steps to launch readiness.</h2>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {steps.map(({ n, title, text }) => (
          <div key={n} className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl border border-cyan/20 bg-cyan/[0.07] text-sm font-black text-cyan">
              {n}
            </div>
            <h3 className="text-lg font-black text-white">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <>
      <Hero />
      <TrustStrip />
      <LaunchSurface />
      <HowItWorks />
      <SampleScannerDemo />
      <TrustBuilderSection />
      <ProductionReadiness />
      <PricingSection />
    </>
  );
}
