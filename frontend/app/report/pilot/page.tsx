import Link from "next/link";
import { ScannerResultsClient } from "@/components/results/ScannerResultsClient";

export const metadata = {
  title: "Pilot Report | Web3Guard AI",
  description: "Generate a pre-audit pilot report from real scanner result evidence with limitations visible.",
};

const reportRules = [
  "Assessed modules and Not Assessed modules stay separate.",
  "External advisories are not counted as Web3Guard-discovered findings.",
  "Static-analysis output remains preliminary until manual triage.",
  "No private key, seed phrase, mnemonic, wallet signing, or exploit automation.",
];

export default function PilotReportPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Pilot report</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">A sellable first-user report without unsafe claims.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Use this pilot report flow for early users and founder feedback. It is a pre-audit readiness report, not a certified audit.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/results" className="btn-primary">Open result engine →</Link>
          <Link href="/pricing" className="btn-secondary">Pricing / ₹999 validation</Link>
          <Link href="/methodology" className="btn-secondary">Methodology</Link>
          <Link href="/pilot-experience" className="btn-secondary">Pilot feedback</Link>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {reportRules.map((item) => (
          <div key={item} className="glass-tile p-5 text-sm leading-6 text-slate-300">{item}</div>
        ))}
      </section>

      <ScannerResultsClient />
    </main>
  );
}
