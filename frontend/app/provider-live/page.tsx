import { ProviderLiveClient } from "@/components/provider-live/ProviderLiveClient";

export default function ProviderLivePage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Phase 28 · Real provider live integration</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-6xl">
          Live providers, clear errors, zero fake intelligence.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Phase 28 connects the provider truth layer for explorer verified source, GitHub metadata, GoPlus readiness, and advisory sources. Missing keys or disabled sources remain visible as Needs API Key / Provider Not Configured / Not Assessed.
        </p>
      </section>
      <ProviderLiveClient />
    </main>
  );
}
