import { Hero } from "@/components/sections/Hero";
import { LaunchSurface } from "@/components/sections/LaunchSurface";
import { PricingSection } from "@/components/sections/PricingSection";
import { TrustStrip } from "@/components/sections/TrustStrip";
import { TrustBuilderSection } from "@/components/sections/TrustBuilderSection";
import { ProductionReadiness } from "@/components/sections/ProductionReadiness";
import { SampleScannerDemo } from "@/components/sections/SampleScannerDemo";

export default function HomePage() {
  return (
    <>
      <Hero />
      <TrustStrip />
      <LaunchSurface />
      <SampleScannerDemo />
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="card grid gap-8 p-8 lg:grid-cols-3">
          {[
            ["1", "Scan", "Paste Solidity, URL, or fill launch checklists."],
            ["2", "Understand", "Get score, severity, business impact, and fix direction."],
            ["3", "Upgrade", "Request paid report or manual pre-audit review via UPI."],
          ].map(([step, title, text]) => (
            <div key={step}>
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan/10 font-black text-cyan">{step}</div>
              <h3 className="text-xl font-black">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
            </div>
          ))}
        </div>
      </section>
      <TrustBuilderSection />
      <ProductionReadiness />
      <PricingSection />
    </>
  );
}
