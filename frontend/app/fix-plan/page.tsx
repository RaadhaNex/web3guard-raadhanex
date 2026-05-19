import Link from "next/link";

const steps = [
  ["1", "Fix critical blockers first", "Access control, upgrade risk, exposed secrets, payment/webhook mistakes, and CISA KEV matches get priority."],
  ["2", "Separate evidence gaps", "Tool Not Installed and Needs API Key are setup tasks, not fake vulnerabilities."],
  ["3", "Re-run after patch", "Generate a new report snapshot only after fixes are verified."],
  ["4", "Escalate to human audit", "Use Web3Guard as pre-audit readiness, not as a replacement for expert review."],
];

export const metadata = {
  title: "Fix Plan | Web3Guard AI",
  description: "Prioritized Web3 launch readiness fix planning with safe pre-audit wording.",
};

export default function FixPlanPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Fix Plan</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Turn scanner output into a launch action plan.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          The fix plan keeps business-critical blockers, evidence gaps, and manual-review items separate so founders know what to do next.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/eon" className="btn-primary">Open EON risk graph →</Link>
          <Link href="/security-tests" className="btn-secondary">Generate defensive tests</Link>
        </div>
      </section>
      <section className="mt-8 grid gap-4 md:grid-cols-2">
        {steps.map(([n, title, text]) => (
          <div key={n} className="glass-tile p-5">
            <p className="mono text-xs font-black text-cyan">STEP {n}</p>
            <p className="mt-2 text-lg font-black text-white">{title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
