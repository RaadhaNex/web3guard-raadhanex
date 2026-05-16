import Link from "next/link";

export default function ReportPage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <p className="text-sm font-black uppercase tracking-[0.3em] text-cyan">professional report layer</p>
      <h1 className="mt-3 text-4xl font-black sm:text-6xl">Combined Launch Readiness + Professional Delivery</h1>
      <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-300">
        Combine Smart Contract, Website, dApp, API, Wallet, and Admin OpSec module outputs into one weighted
        launch readiness report with report hash, coverage confidence, priority action plan, package recommendation,
        before-launch checklist, markdown/JSON export, and print/save-as-PDF delivery.
      </p>
      <div className="mt-8 grid gap-4 md:grid-cols-4">
        <div className="card p-5">
          <p className="font-black text-white">Weighted score</p>
          <p className="mt-2 text-sm text-slate-400">Contract 35%, Website 15%, dApp 15%, API 15%, Wallet 10%, Admin OpSec 10%.</p>
        </div>
        <div className="card p-5">
          <p className="font-black text-white">Coverage confidence</p>
          <p className="mt-2 text-sm text-slate-400">Shows whether the score is full launch readiness or partial available score.</p>
        </div>
        <div className="card p-5">
          <p className="font-black text-white">Client delivery</p>
          <p className="mt-2 text-sm text-slate-400">Print/PDF, markdown, JSON, public-safe wording, and report verification hash.</p>
        </div>
        <div className="card p-5">
          <p className="font-black text-white">No fake claims</p>
          <p className="mt-2 text-sm text-slate-400">Pre-audit readiness only. No certified audit or 100% secure claim.</p>
        </div>
      </div>
      <section className="mt-10 card p-6">
        <h2 className="text-2xl font-black text-white">How to generate final report</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm leading-7 text-slate-300">
          <li>Run one or more scanner modules from the scanner page.</li>
          <li>Click <span className="font-black text-white">Generate Launch Report</span>.</li>
          <li>Review missing modules, severity breakdown, and priority actions.</li>
          <li>Download server-side PDF, branded HTML, Markdown, JSON, or publish a public/private report record.</li>
        </ol>
      </section>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/scanner" className="btn-primary">Start scanner modules</Link>
        <Link href="/report/professional" className="btn-secondary">Professional delivery</Link>
        <Link href="/sample-reports" className="btn-secondary">View sample reports</Link>
        <Link href="/methodology" className="btn-secondary">Read scoring methodology</Link>
      </div>
    </main>
  );
}
