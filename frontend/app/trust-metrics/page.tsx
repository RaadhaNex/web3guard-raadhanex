import { TrustMetricsClient } from "@/components/trust-metrics/TrustMetricsClient";

export default function TrustMetricsPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Phase 29 · Trust metrics engine</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-6xl">
          Public trust metrics without fake discovery claims.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Phase 29 separates external advisories, Web3Guard-generated findings, community review items, and disclosure lifecycle records so public metrics stay useful, honest, and legally safe.
        </p>
      </section>
      <TrustMetricsClient />
    </main>
  );
}
