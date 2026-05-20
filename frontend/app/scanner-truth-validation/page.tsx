import { ScannerTruthValidationClient } from "@/components/scanner-truth/ScannerTruthValidationClient";

export const dynamic = "force-dynamic";

export default function ScannerTruthValidationPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan/15 bg-slate-950/75 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <p className="section-label">Scanner Truth Validation</p>
        <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Prove real scanner output before adding more features.
        </h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
          Phase 44 checks the latest unified scan payload for evidence mapping, missing-state honesty, report/export readiness, and fake-claim blockers. It does not reinstall Slither/Semgrep or create fake findings.
        </p>
      </section>
      <ScannerTruthValidationClient />
    </main>
  );
}
