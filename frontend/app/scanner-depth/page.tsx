import { ScannerDepthClient } from "@/components/scanner-depth/ScannerDepthClient";

export default function ScannerDepthPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="clean-panel p-6 sm:p-8">
        <p className="section-label">Phase 38 · Real scanner depth hardening</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Push scanner coverage toward 90% without fake security guarantees.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          This page turns Slither, Semgrep, OSV, CISA KEV, GitHub hygiene, Foundry, Echidna, Mythril, and evidence/report completeness into one honest pre-audit coverage model. It never claims 99% security or certified audit status.
        </p>
      </section>
      <ScannerDepthClient />
    </main>
  );
}
