import Link from "next/link";
import { ScannerResultsClient } from "@/components/results/ScannerResultsClient";

const visibleStates = [
  ["Assessed", "A configured tool, imported evidence, or safe backend rule reviewed this area."],
  ["Not Assessed", "No evidence is available, so Web3Guard does not guess or fake a pass."],
  ["Tool Not Installed", "A scanner exists, but the backend worker/tool is not installed or enabled."],
  ["Needs API Key", "A provider can help, but the required API key is not configured yet."],
  ["Manual Review", "Founder or reviewer must verify before launch decisions."],
];

const outputCards = [
  ["Findings", "Only real findings from supplied evidence, configured tools, or safe backend rules."],
  ["Gaps", "Missing evidence stays visible as Not Assessed / Manual / Provider Not Configured."],
  ["Actions", "Priority fixes tell founders what to handle before a professional audit."],
  ["Report path", "Move clean evidence into the ₹999 pilot readiness report flow when ready."],
];

export const metadata = {
  title: "Results | Web3Guard AI",
  description: "Clear Web3Guard results screen for assessed evidence, missing modules, setup states, and report actions.",
};

export default function ResultsPage() {
  return (
    <main className="results-final-page mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="results-final-hero scroll-motion-ready">
        <div>
          <p className="video-section-kicker">Results</p>
          <h1>Results appear here after a scan.</h1>
          <p>
            If no scan is selected yet, this screen still explains exactly what users will see: evidence-backed findings, missing coverage, and next actions.
          </p>
          <div className="results-action-row">
            <Link href="/scanner/unified-url" className="video-hero-primary">Run readiness scan →</Link>
            <Link href="/report" className="video-hero-secondary">Open report center</Link>
          </div>
        </div>
        <aside className="results-empty-preview" aria-label="No active scan selected">
          <span>No active scan selected</span>
          <strong>Ready for evidence</strong>
          <p>Run a scan or open a saved scan to populate this page with real modules and findings.</p>
        </aside>
      </section>

      <section className="results-state-strip scroll-motion-ready" aria-label="Result states">
        {visibleStates.map(([title, text]) => (
          <article key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>

      <section className="results-output-grid">
        {outputCards.map(([title, text]) => (
          <article key={title} className="results-output-card scroll-motion-ready">
            <span>{title}</span>
            <p>{text}</p>
          </article>
        ))}
      </section>

      <section className="results-preview-console scroll-motion-ready">
        <div className="results-preview-head">
          <div>
            <p className="video-section-kicker">Optional preview</p>
            <h2>Evidence console</h2>
          </div>
          <p>Use this only for test payloads or supplied evidence. It does not create fake scan results.</p>
        </div>
        <ScannerResultsClient />
      </section>
    </main>
  );
}
