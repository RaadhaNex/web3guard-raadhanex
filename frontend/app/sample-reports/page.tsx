import Link from "next/link";
import { reportSamples } from "@/lib/trustContent";

export default function SampleReportsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Sample reports</p>
      <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Report templates that sell trust without overclaiming.</h1>
      <p className="mt-4 max-w-3xl text-slate-400">
        These samples show how paid reports can explain launch risk, founder impact, developer fixes, and next actions while keeping the correct disclaimer.
      </p>
      <div className="mt-10 grid gap-5 md:grid-cols-2">
        {reportSamples.map((sample) => (
          <div key={sample.id} className="card p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <span className="badge">{sample.projectType}</span>
                <h2 className="mt-4 text-xl font-black">{sample.title}</h2>
              </div>
              <div className="rounded-2xl border border-cyan/20 bg-cyan/10 px-4 py-3 text-center">
                <div className="mono text-2xl font-black text-cyan">{sample.score}</div>
                <div className="text-xs text-slate-400">score</div>
              </div>
            </div>
            <p className="mt-3 text-sm font-bold text-amber-100">{sample.risk}</p>
            <p className="mt-3 text-sm leading-6 text-slate-400">{sample.summary}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {sample.highlights.map((item) => <span key={item} className="badge">{item}</span>)}
            </div>
            <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">Recommended: {sample.package}</div>
          </div>
        ))}
      </div>
      <div className="mt-10 flex flex-wrap gap-3">
        <Link href="/report" className="btn-primary">Open Report Builder</Link>
        <Link href="/contact" className="btn-secondary">Request Paid Review</Link>
      </div>
    </div>
  );
}
