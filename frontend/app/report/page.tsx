import Link from "next/link";

const reportSections = [
  ["Surface summary", "Website, dApp, API, GitHub, wallet UX, contract, and admin OpSec remain separated."],
  ["Evidence states", "Assessed, Not Assessed, Needs API Key, Tool Not Installed, and Manual Review stay visible."],
  ["Fix path", "Priority actions explain what to fix before a professional audit or public launch."],
  ["Export path", "PDF, HTML, Markdown, and JSON can be used when backend report data exists."],
];

const flow = [
  ["01", "Scan", "Submit the URL and optional evidence."],
  ["02", "Review", "Check findings, gaps, and setup states."],
  ["03", "Report", "Prepare the pilot readiness report path."],
];

export const metadata = {
  title: "Report | Web3Guard AI",
  description: "Clear Web3Guard report center for founder-ready pre-audit readiness reports and export flow.",
};

export default function ReportPage() {
  return (
    <main className="report-final-page mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="report-final-hero scroll-motion-ready">
        <div>
          <p className="video-section-kicker">Report</p>
          <h1>Report center is ready when scan evidence exists.</h1>
          <p>
            This page explains the report path even before a scan is selected. Generated reports must stay pre-audit only, evidence-first, and honest about missing coverage.
          </p>
          <div className="results-action-row">
            <Link href="/scanner/unified-url" className="video-hero-primary">Run scan →</Link>
            <Link href="/payment-validation" className="video-hero-secondary">₹999 validation</Link>
            <Link href="/report/professional" className="video-hero-secondary">Export builder</Link>
          </div>
        </div>
        <aside className="report-document-preview" aria-label="Report preview">
          <div className="report-doc-top">
            <span>WG-REPORT</span>
            <b>Pre-audit only</b>
          </div>
          <strong>Founder readiness report</strong>
          <p>No certified audit claim. No 100% secure claim. No fake score.</p>
          <div className="report-doc-lines"><i /><i /><i /><i /></div>
        </aside>
      </section>

      <section className="report-section-grid">
        {reportSections.map(([title, text]) => (
          <article key={title} className="report-section-card scroll-motion-ready">
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>

      <section className="report-flow-card scroll-motion-ready">
        <div>
          <p className="video-section-kicker">Flow</p>
          <h2>Scan → Results → Report</h2>
        </div>
        <div className="report-flow-mini-grid">
          {flow.map(([number, title, text]) => (
            <article key={number}>
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="report-boundary-simple scroll-motion-ready">
        <article>
          <h2>Report includes</h2>
          <p>Evidence summary, Not Assessed modules, priority fixes, limitations, and export-ready structure.</p>
        </article>
        <article>
          <h2>Report does not claim</h2>
          <p>Certified audit, penetration test, exploit-proof status, insurance guarantee, or complete vulnerability coverage.</p>
        </article>
      </section>
    </main>
  );
}
