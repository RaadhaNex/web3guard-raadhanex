import Link from "next/link";

const sampleRows = [
  { surface: "Contract", status: "Sample", result: "Owner power and upgrade safety require manual review before launch." },
  { surface: "Website", status: "Sample", result: "CSP/HSTS preview shown as launch-readiness guidance, not live evidence." },
  { surface: "Wallet flow", status: "Sample", result: "Unlimited approval warning copy should be visible to users." },
  { surface: "API/Admin", status: "Not Assessed", result: "Needs real endpoint, auth model, logs, and owner-approved scope." },
];

export function SampleScannerDemo() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Sample scanner demo</p>
          <h2 className="mt-3 text-3xl font-black">Try the flow without fake live claims.</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            The homepage preview is clearly labelled as sample. Real results come only from scanner APIs, installed tools, configured providers, or manual/admin evidence.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Run real URL scan</Link>
            <Link href="/scanner/static-analysis" className="btn-secondary">Run tool-gated static scan</Link>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.25em] text-amber-200">Score preview marked sample</p>
              <p className="mt-2 text-5xl font-black">82<span className="text-xl text-slate-500">/100</span></p>
            </div>
            <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-4 py-2 text-sm font-bold text-amber-100">Sample only</span>
          </div>
          <div className="mt-6 grid gap-3">
            {sampleRows.map((row) => (
              <div key={row.surface} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-bold text-white">{row.surface}</p>
                  <span className={row.status === "Not Assessed" ? "rounded-full border border-slate-400/30 px-3 py-1 text-xs text-slate-300" : "rounded-full border border-amber-400/30 px-3 py-1 text-xs text-amber-100"}>{row.status}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">{row.result}</p>
              </div>
            ))}
          </div>
          <p className="mt-5 text-xs leading-5 text-slate-500">No fake counters, testimonials, certified-audit badges, or “100% secure” claims are displayed.</p>
        </div>
      </div>
    </section>
  );
}
