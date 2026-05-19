import Link from "next/link";
import { ScannerResultsClient } from "@/components/results/ScannerResultsClient";

const states = [
  ["Assessed", "A real rule, tool, provider, or supplied evidence produced a check."],
  ["Not Assessed", "The module was not checked and must not be treated as passed."],
  ["Tool Not Installed", "The worker/runtime does not have the required tool available."],
  ["Needs API Key", "The provider exists, but backend credentials are not configured."],
  ["Provider Not Configured", "External provider checks are intentionally unavailable until setup is complete."],
  ["Manual Review Required", "Human review is needed before launch or payment decisions."],
];

export const metadata = {
  title: "Results | Web3Guard AI",
  description: "Normalize scanner findings, advisories, risk intelligence, Not Assessed modules, and pilot report output without fake certainty.",
};

export default function ResultsPage() {
  return (
    <main className="cinematic-page-shell mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="cinematic-page-hero clean-panel cinematic-panel p-6 sm:p-8">
        <p className="section-label">Results</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">Real results with visible gaps.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Understand exactly what was assessed, what was not assessed, what needs a configured provider, and where manual review is still required.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Run scanner →</Link>
          <Link href="/report" className="btn-secondary">Report flow</Link>
          <Link href="/risk-intelligence" className="btn-secondary">Risk intelligence</Link>
          <Link href="/dashboard/scans" className="btn-secondary">Saved scans</Link>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {states.map(([title, text]) => (
          <div key={title} className="glass-tile cinematic-card p-5">
            <p className="text-lg font-black text-white">{title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </section>

      <div className="mt-8 rounded-[28px] border border-white/[0.07] bg-black/20 p-1 shadow-[0_24px_90px_rgba(0,0,0,.35)]">
        <ScannerResultsClient />
      </div>
    </main>
  );
}
