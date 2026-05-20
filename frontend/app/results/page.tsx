import Link from "next/link";
import { ScannerResultsClient } from "@/components/results/ScannerResultsClient";

const resultStates = [
  {
    title: "Assessed",
    label: "Evidence found",
    text: "A configured tool, imported evidence, or safe backend rule reviewed this area.",
  },
  {
    title: "Not Assessed",
    label: "No guessing",
    text: "No evidence was supplied, so Web3Guard keeps the module visible instead of inventing a pass.",
  },
  {
    title: "Needs API Key",
    label: "Provider missing",
    text: "The provider exists but cannot run until the backend is configured with the required key.",
  },
  {
    title: "Manual Review",
    label: "Human check",
    text: "Launch-critical decisions stay marked for founder or reviewer verification.",
  },
];

const signalCards = [
  ["Findings", "Real issues only", "Imported Slither, safe dependency signals, and backend rules stay traceable."],
  ["Gaps", "Visible missing coverage", "Unavailable tools become Not Assessed, Tool Not Installed, or Provider Not Configured."],
  ["Actions", "Prioritized fix path", "The result screen separates blockers, next fixes, and report-ready evidence."],
];

export const metadata = {
  title: "Results | Web3Guard AI",
  description: "Premium result console for Web3Guard AI pre-audit readiness findings, gaps, and report actions.",
};

export default function ResultsPage() {
  return (
    <main className="results-cinematic-page">
      <section className="results-hero-shell mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="results-hero-grid">
          <div className="results-hero-copy scroll-motion-ready">
            <p className="video-section-kicker">RESULT CONSOLE</p>
            <h1>Readiness results without fake confidence.</h1>
            <p>
              See what Web3Guard actually assessed, what stayed unassessed, and what should move into the ₹999 pilot report path.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="video-hero-primary">Run new scan →</Link>
              <Link href="/report" className="video-hero-secondary">Open report center</Link>
            </div>
          </div>

          <div className="result-orb-panel scroll-motion-ready" aria-hidden="true">
            <div className="result-orb-glow" />
            <div className="result-orb-core">WG</div>
            <span className="result-orbit result-orbit-one" />
            <span className="result-orbit result-orbit-two" />
            <span className="result-signal-dot result-signal-dot-a" />
            <span className="result-signal-dot result-signal-dot-b" />
            <span className="result-signal-dot result-signal-dot-c" />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-10 sm:px-6 lg:px-8">
        <div className="result-state-grid">
          {resultStates.map((item) => (
            <article key={item.title} className="result-state-card scroll-motion-ready">
              <span>{item.label}</span>
              <h2>{item.title}</h2>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <div className="results-signal-strip scroll-motion-ready">
          {signalCards.map(([title, label, text]) => (
            <article key={title}>
              <span>{label}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <ScannerResultsClient />
      </section>
    </main>
  );
}
