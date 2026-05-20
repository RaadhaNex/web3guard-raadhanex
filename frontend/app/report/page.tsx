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
      <section className="grid gap-5 rounded-[2rem] border border-cyan-300/15 bg-slate-950/70 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8 lg:grid-cols-[1fr_380px]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-200/80">Report</p>
          <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">Report center is visible and ready.</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
            Generated reports must stay pre-audit only, evidence-first, and honest about missing coverage. Run a scan first, then prepare the report path.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="rounded-full bg-cyan-200 px-5 py-3 text-sm font-black text-slate-950 transition hover:-translate-y-0.5">Run scan →</Link>
            <Link href="/payment-validation" className="rounded-full border border-white/10 bg-white/[0.06] px-5 py-3 text-sm font-black text-white transition hover:-translate-y-0.5">₹999 validation</Link>
            <Link href="/report/professional" className="rounded-full border border-white/10 bg-white/[0.06] px-5 py-3 text-sm font-black text-white transition hover:-translate-y-0.5">Export builder</Link>
          </div>
        </div>
        <aside className="rounded-[1.5rem] border border-white/10 bg-white/[0.04] p-5">
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs font-black uppercase tracking-[0.18em] text-cyan-200">WG-REPORT</span>
            <b className="rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-amber-100">Pre-audit only</b>
          </div>
          <strong className="mt-5 block text-3xl font-black tracking-[-0.05em] text-white">Founder readiness report</strong>
          <p className="mt-3 text-sm leading-7 text-slate-300">No certified audit claim. No 100% secure claim. No fake score.</p>
          <div className="mt-6 grid gap-3">
            <i className="h-3 rounded-full bg-cyan-200/45" />
            <i className="h-3 w-10/12 rounded-full bg-purple-300/30" />
            <i className="h-3 w-8/12 rounded-full bg-blue-300/25" />
          </div>
        </aside>
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-4">
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
