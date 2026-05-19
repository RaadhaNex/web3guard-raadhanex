import Link from "next/link";

const coreDocs = [
  ["Methodology", "/methodology", "How readiness scoring, evidence, confidence, and Not Assessed states work."],
  ["Limitations", "/limitations", "What Web3Guard does not claim and where manual security review is still required."],
  ["Responsible Use", "/responsible-use", "No private keys, no wallet signing, no exploit automation, and no unauthorized scanning."],
  ["Scope & Refund", "/scope-refund", "How to keep paid pilot-report scope clear for early users."],
];

const setupDocs = [
  ["Provider Live", "/provider-live", "Explorer, advisory, GitHub, and external-provider readiness states."],
  ["Worker Execution", "/worker-execution", "Slither, Semgrep, Foundry, Echidna, Mythril, and worker status boundaries."],
  ["Payment Validation", "/payment-validation", "Razorpay/UPI test flow, verification, webhook, and audit-log status."],
  ["Launch Pack", "/launch-pack", "First 10 users checklist, outreach, public beta wording, and safe launch guardrails."],
  ["Trust Metrics", "/trust-metrics", "Public-safe metrics, disclosures, and no fake discovery claims."],
  ["Advanced Tools", "/advanced", "All non-core modules moved away from the main navigation."],
];

export const metadata = {
  title: "Docs | Web3Guard AI",
  description: "Web3Guard methodology, limitations, responsible use, provider setup, and launch validation docs.",
};

export default function DocsPage() {
  return (
    <main className="cinematic-page-shell mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="cinematic-page-hero clean-panel cinematic-panel p-6 sm:p-8">
        <p className="section-label">Docs</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">Everything users need to trust the beta.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Main navigation stays simple. Technical setup, advanced modules, provider status, and limitations stay organized here.
        </p>
      </section>

      <section className="mt-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="section-label">Core trust docs</p>
            <h2 className="mt-2 text-2xl font-black text-white">Show these to beta users first.</h2>
          </div>
          <Link href="/responsible-use" className="btn-secondary">Responsible use →</Link>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {coreDocs.map(([title, href, text]) => (
            <Link key={href} href={href} className="glass-tile cinematic-card block p-5 transition hover:-translate-y-1">
              <p className="text-lg font-black text-white">{title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
              <p className="mt-4 text-xs font-bold text-cyan">Open →</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <p className="section-label">Setup and advanced</p>
        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {setupDocs.map(([title, href, text]) => (
            <Link key={href} href={href} className="glass-tile cinematic-card block p-5 transition hover:-translate-y-1">
              <p className="text-lg font-black text-white">{title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
              <p className="mt-4 text-xs font-bold text-cyan">Open →</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
