import { WorkerRunsClient } from "@/components/worker-runs/WorkerRunsClient";

export default function WorkerRunsPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Phase 33 · Real worker execution depth</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-6xl">
          Run real worker evidence, or clearly show Not Assessed.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Phase 33 connects the static worker result engine to real Slither/Aderyn/Semgrep execution when configured, adds imported JSON normalization for Foundry, Echidna, and Mythril, and keeps every missing tool as status-only instead of fake findings.
        </p>
      </section>
      <WorkerRunsClient />
    </main>
  );
}
