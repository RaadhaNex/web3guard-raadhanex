import Link from "next/link";

const reportModules = [
  ["Surface summary", "Website, dApp, API, GitHub, wallet UX, contract, and admin OpSec stay separated."],
  ["Evidence states", "Assessed, Not Assessed, Needs API Key, Tool Not Installed, and Manual Review remain visible."],
  ["Fix path", "Founder-friendly priorities explain what to fix before paying for deeper manual review."],
  ["Export path", "PDF, HTML, Markdown, and JSON remain report outputs when backend payload is available."],
];

const flow = [
  ["01", "Scan", "Run the readiness scan with URL and optional evidence."],
  ["02", "Review", "Check findings, missing coverage, provider states, and launch blockers."],
  ["03", "Report", "Generate a pilot readiness report without audit-company claims."],
];

export const metadata = {
  title: "Report | Web3Guard AI",
  description: "Premium report center for Web3Guard AI pre-audit readiness reports and export flow.",
};

export default function ReportPage() {
  return (
    <main className="report-cinematic-page">
      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="report-hero-grid">
          <div className="report-hero-copy scroll-motion-ready">
            <p className="video-section-kicker">REPORT CENTER</p>
            <h1>Turn scan evidence into a founder-ready report.</h1>
            <p>
              Web3Guard reports are built for pre-audit launch decisions: clear evidence, visible gaps, practical fixes, and safe wording.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="video-hero-primary">Run scan →</Link>
              <Link href="/report/pilot" className="video-hero-secondary">Pilot report</Link>
              <Link href="/report/professional" className="video-hero-secondary">Export builder</Link>
            </div>
          </div>

          <aside className="report-preview-shell scroll-motion-ready" aria-label="Report preview">
            <div className="report-preview-top">
              <span>WG-REPORT</span>
              <b>Pre-audit only</b>
            </div>
            <div className="report-preview-score">
              <span>Readiness</span>
              <strong>Evidence first</strong>
              <p>No fake pass. No certified audit claim. No security guarantee.</p>
            </div>
            <div className="report-preview-lines">
              <span />
              <span />
              <span />
              <span />
            </div>
          </aside>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <div className="report-module-grid">
          {reportModules.map(([title, text]) => (
            <article key={title} className="report-module-card scroll-motion-ready">
              <h2>{title}</h2>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-14 sm:px-6 lg:px-8">
        <div className="report-flow-shell scroll-motion-ready">
          <div>
            <p className="video-section-kicker">FLOW</p>
            <h2>Scan → Results → Report</h2>
          </div>
          <div className="report-flow-grid">
            {flow.map(([number, title, text]) => (
              <article key={number}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="report-boundary-card scroll-motion-ready">
          <div>
            <p className="video-section-kicker">TRUST BOUNDARY</p>
            <h2>Useful for founders, honest for users.</h2>
          </div>
          <div className="report-boundary-grid">
            <article>
              <h3>Report includes</h3>
              <p>Evidence summary, Not Assessed modules, priority fixes, limitations, and export-ready structure.</p>
            </article>
            <article>
              <h3>Report does not claim</h3>
              <p>Certified audit, penetration test, exploit-proof status, insurance guarantee, or complete vulnerability coverage.</p>
            </article>
          </div>
        </div>
      </section>
    </main>
  );
}
