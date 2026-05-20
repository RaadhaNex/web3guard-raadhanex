import { ScannerCorrelationClient } from "@/components/scanner-correlation/ScannerCorrelationClient";

export const metadata = {
  title: "Scanner Correlation Engine | Web3Guard AI",
  description: "Prioritize findings across scanner outputs, CVE/CWE context, exposure, and attack-path risk without destructive exploitation.",
};

export default function ScannerCorrelationPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="clean-panel p-6 sm:p-8">
        <p className="section-label">Phase 43 · Scanner Correlation Engine</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Turn many scanner findings into clear launch blockers and attack-path priorities.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Web3Guard correlates Slither, Semgrep, OSV/NVD/CISA, OpenZeppelin pattern intelligence, Web DAST baseline, and manual context into P0/P1/P2/P3 priorities. This does not run exploitation, does not guarantee all bugs are found, and is not a certified audit.
        </p>
      </section>

      <ScannerCorrelationClient />
    </main>
  );
}
