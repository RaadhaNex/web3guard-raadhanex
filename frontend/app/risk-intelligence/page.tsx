import { RiskIntelligenceClient } from "@/components/risk-intelligence/RiskIntelligenceClient";

export const metadata = {
  title: "Risk Intelligence | Web3Guard AI",
  description: "CWE/NVD-aware pre-audit risk intelligence with impact, future risk, exploit scenario, and fix plan without all-bug guarantees.",
};

export default function RiskIntelligencePage() {
  return (
    <main className="cinematic-page-shell mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="cinematic-page-hero clean-panel cinematic-panel p-6 sm:p-8">
        <p className="section-label">Advanced Risk Intelligence Engine</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Explain bugs like a security analyst, not a fake all-bug scanner.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Web3Guard maps scanner/provider/manual findings to CWE/NVD-aware impact, future risk, exploit scenario, fix plan, verification steps, and coverage gaps. It never claims every bug is found.
        </p>
      </section>

      <div className="mt-8 rounded-[28px] border border-white/[0.07] bg-black/20 p-1 shadow-[0_24px_90px_rgba(0,0,0,.35)]">
        <RiskIntelligenceClient />
      </div>
    </main>
  );
}
