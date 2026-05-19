import Link from "next/link";

const states = [
  ["Assessed", "A real rule, tool, or provider produced evidence."],
  ["Not assessed yet", "No evidence was supplied or live provider lookup was not requested."],
  ["Needs API Key", "Provider exists, but required backend key is missing."],
  ["Tool Not Installed", "External tool was not found on the worker/runtime."],
  ["Manual review required", "Human review is required; Web3Guard will not fake certainty."],
];

export const metadata = {
  title: "Results | Web3Guard AI",
  description: "Understand Web3Guard assessed, not assessed, provider, and manual-review result states.",
};

export default function ResultsPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Results</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Clear outputs, no fake security certainty.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Web3Guard separates real evidence from missing evidence. A missing provider/tool is not counted as a fake pass or fake fail.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Run scanner →</Link>
          <Link href="/dashboard/scans" className="btn-secondary">Saved scans</Link>
        </div>
      </section>
      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {states.map(([title, text]) => (
          <div key={title} className="glass-tile p-5">
            <p className="text-lg font-black text-white">{title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
