export default function TermsPage() {
  const terms = [
    "Web3Guard AI provides preliminary security readiness guidance only.",
    "Automated scanner output is not a certified audit and is not a guarantee of security.",
    "Users are responsible for confirming they own or are authorized to review submitted projects.",
    "Paid reports and manual review are limited to the agreed package scope and submitted material.",
    "No investment, financial, legal, tax, or regulatory advice is provided.",
    "RAADHANEX can reject unsafe, unauthorized, illegal, or out-of-scope requests.",
  ];
  return (
    <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Terms</p>
      <h1 className="mt-3 text-4xl font-black sm:text-5xl">Terms of service summary.</h1>
      <p className="mt-4 text-slate-400">Replace this with lawyer-reviewed terms before public commercial launch. This page gives the product-safe MVP baseline.</p>
      <div className="card mt-10 p-6"><ul className="space-y-4 text-sm leading-6 text-slate-300">{terms.map((x) => <li key={x}>• {x}</li>)}</ul></div>
      <div className="mt-8 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100">Before production, get proper legal review for jurisdiction, refunds, liability limits, data processing, and payment terms.</div>
    </div>
  );
}
