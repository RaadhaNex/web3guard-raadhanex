import { ProviderReadinessClient } from "@/components/provider-readiness/ProviderReadinessClient";

export default function ProviderReadinessPage() {
  return (
    <main>
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="quantum-stage p-6 sm:p-8">
          <p className="section-label">Phase 10 · External provider readiness</p>
          <h1 className="mt-3 max-w-5xl text-4xl font-black sm:text-6xl">
            Etherscan, GoPlus, and GitHub provider truth board.
          </h1>
          <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
            Connect real provider keys when you are ready. Until then, Web3Guard keeps every missing provider visible as Needs API Key or Provider Not Configured.
          </p>
        </div>
      </section>
      <ProviderReadinessClient />
    </main>
  );
}
