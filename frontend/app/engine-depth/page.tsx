import { EngineDepthClient } from "@/components/engine-depth/EngineDepthClient";

export default function EngineDepthPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Phase 9 · Real engine depth</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-6xl">
          Real tools only. Missing engines stay visible.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          This board shows which static analyzers, deep analyzers, and provider integrations are ready on the deployed backend. Web3Guard does not fake Slither, Aderyn, Mythril, Etherscan, GoPlus, or GitHub evidence.
        </p>
      </section>
      <EngineDepthClient />
    </main>
  );
}
