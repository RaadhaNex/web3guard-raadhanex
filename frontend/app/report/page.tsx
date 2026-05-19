import Link from "next/link";

const reportBlocks = [
  ["Split readiness", "Website, contract, GitHub, API, wallet, and admin evidence stay separated."],
  ["Evidence trail", "Every report keeps assessed evidence, setup gaps, and limitations visible."],
  ["Export formats", "PDF, HTML, Markdown, and JSON are generated from the same report payload."],
  ["Safe wording", "Reports stay pre-audit readiness reviews and never imply certification."],
];

const flow = [
  ["01", "Run scanner", "Start with Unified Launch Scan or a focused module."],
  ["02", "Review evidence", "Check findings, severity, missing modules, and confidence basis."],
  ["03", "Export report", "Download artifacts or save records for dashboard/history."],
];

export default function ReportPage() {
  return (
    <main className="cinematic-page-shell relative overflow-hidden">
      <section className="cinematic-page-hero mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-end">
          <div>
            <p className="section-label">Report</p>
            <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
              A premium readiness report, not an audit certificate.
            </h1>
            <p className="mt-5 max-w-3xl text-base leading-8 text-slate-300 sm:text-lg">
              Turn scanner output into a professional pre-audit readiness report with traceable evidence, fix guidance, export artifacts, and clear limitations.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="btn-primary">Run unified scan →</Link>
              <Link href="/report/professional" className="btn-secondary">Professional delivery</Link>
              <Link href="/report/pilot" className="btn-secondary">Pilot report</Link>
              <Link href="/sample-reports" className="btn-secondary">Sample reports</Link>
            </div>
          </div>

          <div className="clean-panel cinematic-panel p-5">
            <div className="flex items-center justify-between border-b border-white/[0.07] pb-4">
              <p className="mono text-xs font-bold uppercase tracking-[0.16em] text-cyan">report.boundary</p>
              <span className="badge badge-amber">Pre-audit only</span>
            </div>
            <div className="mt-5 grid gap-3">
              {reportBlocks.map(([title, text]) => (
                <div key={title} className="cinematic-mini-card p-4">
                  <p className="font-black text-white">{title}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="cinematic-band border-y border-cyan/10">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <p className="section-label">Workflow</p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {flow.map(([number, title, text]) => (
              <div key={number} className="card cinematic-card p-6">
                <p className="mono text-4xl font-black text-cyan/25">{number}</p>
                <h2 className="mt-4 text-xl font-black text-white">{title}</h2>
                <p className="mt-3 text-sm leading-6 text-slate-400">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="card cinematic-panel p-6 sm:p-8">
          <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div>
              <p className="section-label">Trust boundary</p>
              <h2 className="mt-3 text-3xl font-black text-white">What the report is and is not.</h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-5 shadow-[0_18px_60px_rgba(16,185,129,.08)]">
                <p className="font-black text-emerald-100">It is</p>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-emerald-100/85">
                  <li>• A pre-audit readiness report</li>
                  <li>• Evidence-based and exportable</li>
                  <li>• Useful before paid manual review</li>
                </ul>
              </div>
              <div className="rounded-2xl border border-amber-300/20 bg-amber-300/10 p-5 shadow-[0_18px_60px_rgba(251,191,36,.08)]">
                <p className="font-black text-amber-100">It is not</p>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-100/85">
                  <li>• A certified audit</li>
                  <li>• A guarantee of security</li>
                  <li>• A replacement for professional review</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
