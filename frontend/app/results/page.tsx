import Link from "next/link";

const states = [
  ["Assessed", "A configured tool, safe backend check, or supplied evidence reviewed this area."],
  ["Not Assessed", "No evidence is available, so Web3Guard does not guess or fake a pass."],
  ["Tool Not Installed", "A scanner exists, but the required worker/tool is not installed yet."],
  ["Needs API Key", "A provider can help, but the required key is not configured."],
  ["Manual Review", "Founder or reviewer must verify before launch decisions."],
];

const outputs = [
  ["Findings", "Only real findings from supplied evidence, configured tools, or safe backend rules."],
  ["Coverage gaps", "Missing modules stay visible as Not Assessed, Manual, or Provider Not Configured."],
  ["Priority actions", "Short fixes that help founders prepare before a professional audit."],
  ["Report path", "Move clean evidence into the ₹999 pilot readiness report path when ready."],
];

export const metadata = {
  title: "Results | Web3Guard AI",
  description: "Visible Web3Guard AI results screen for assessed evidence, missing modules, setup states, and report actions.",
};

export default function ResultsPage() {
  return (
    <main className="results-final-page mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/70 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-200/80">Results</p>
        <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">Results screen is visible and ready.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
          Run a scan or open a saved scan to populate this page with real findings. Until then, this page explains exactly what users will see.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="rounded-full bg-cyan-200 px-5 py-3 text-sm font-black text-slate-950 transition hover:-translate-y-0.5">Run readiness scan →</Link>
          <Link href="/report" className="rounded-full border border-white/10 bg-white/[0.06] px-5 py-3 text-sm font-black text-white transition hover:-translate-y-0.5">Open report center</Link>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5" aria-label="Result states">
        {states.map(([title, text]) => (
          <article key={title} className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
            <h2 className="text-xl font-black text-white">{title}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-300">{text}</p>
          </article>
        ))}
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-4" aria-label="Result output types">
        {outputs.map(([title, text]) => (
          <article key={title} className="rounded-[1.5rem] border border-cyan-300/15 bg-cyan-300/[0.04] p-5 shadow-2xl shadow-black/20">
            <span className="text-xs font-black uppercase tracking-[0.22em] text-cyan-200">{title}</span>
            <p className="mt-3 text-sm leading-7 text-slate-300">{text}</p>
          </article>
        ))}
      </section>

      <section className="mt-5 rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5 text-sm leading-7 text-slate-300">
        <b className="text-white">No active scan selected.</b> This is not a fake sample result. Real scan output should come from the scanner or saved scans only.
      </section>
    </main>
  );
}
