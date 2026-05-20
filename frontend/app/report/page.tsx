import Link from "next/link";

const sections = [
  ["Surface summary", "Website, dApp, API, GitHub, wallet UX, contract, and admin OpSec remain separated."],
  ["Evidence states", "Assessed, Not Assessed, Needs API Key, Tool Not Installed, and Manual Review stay visible."],
  ["Fix path", "Priority actions explain what to handle before a professional audit or launch decision."],
  ["Export path", "PDF, HTML, Markdown, and JSON exports should only use real backend report data."],
];

export const metadata = {
  title: "Report | Web3Guard AI",
  description: "Visible Web3Guard AI report center for founder-ready pre-audit readiness reports.",
};

export default function ReportPage() {
  return (
    <main className="report-final-page mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="report-clean-actions">
        <Link href="/scanner/unified-url" className="btn-primary">Run scan →</Link>
        <Link href="/payment-validation" className="btn-secondary">₹999 validation</Link>
        <Link href="/report/professional" className="btn-secondary">Export builder</Link>
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-4">
        {sections.map(([title, text]) => (
          <article key={title} className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
            <h2 className="text-xl font-black text-white">{title}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-300">{text}</p>
          </article>
        ))}
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-2">
        <article className="rounded-[1.5rem] border border-cyan-300/15 bg-cyan-300/[0.04] p-5">
          <h2 className="text-2xl font-black text-white">Report includes</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">Evidence summary, Not Assessed modules, priority fixes, limitations, and export-ready structure.</p>
        </article>
        <article className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-2xl font-black text-white">Report does not claim</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">Certified audit, penetration test, exploit-proof status, insurance guarantee, or complete vulnerability coverage.</p>
        </article>
      </section>
    </main>
  );
}
