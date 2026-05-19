import Link from "next/link";
import { ScannerResultsClient } from "@/components/results/ScannerResultsClient";

const states = [
  ["Assessed", "A real rule, tool, or provider produced evidence."],
  ["Not assessed yet", "No evidence was supplied or live provider lookup was not requested."],
  ["Needs API Key", "Provider exists, but required backend key is missing."],
  ["Tool Not Installed", "External tool was not found on the worker/runtime."],
  ["Manual review required", "Human review is required; Web3Guard will not fake certainty."],
];

export const metadata = {
  title: "Results | Web3Guard AI",
  description: "Normalize scanner findings, OSV/CISA advisories, Not Assessed modules, and pilot report output without fake certainty.",
};

export default function ResultsPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Results</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Real scanner results, pilot reports, and no fake pass.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Phase 32 turns static-analysis output, imported Slither JSON, dependency advisories, missing provider states, and fix priorities into one clean result model.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Run scanner →</Link>
          <Link href="/report/pilot" className="btn-secondary">Pilot report page</Link>
          <Link href="/dashboard/scans" className="btn-secondary">Saved scans</Link>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {states.map(([title, text]) => (
          <div key={title} className="glass-tile p-5">
            <p className="text-lg font-black text-white">{title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </section>

      <ScannerResultsClient />
    </main>
  );
}
