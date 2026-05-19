import { WorkerExecutionClient } from "@/components/worker-execution/WorkerExecutionClient";

export default function WorkerExecutionPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Phase 27 · Real worker execution</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-6xl">
          Isolated workers, real output, no fake scanner evidence.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Phase 27 prepares Slither, Aderyn, Semgrep, Foundry, Echidna, and Mythril for truthful worker execution. Missing binaries or providers remain visible as Tool Not Installed / Provider Not Configured / Manual / Not Assessed.
        </p>
      </section>
      <WorkerExecutionClient />
    </main>
  );
}
