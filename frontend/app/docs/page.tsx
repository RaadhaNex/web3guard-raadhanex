import Link from "next/link";

const docs = [
  ["Methodology", "/methodology", "How readiness scoring, evidence, confidence, and Not Assessed states work."],
  ["Limitations", "/limitations", "What Web3Guard does not claim and where manual audit is still required."],
  ["Responsible Use", "/responsible-use", "No private keys, no wallet signing, no exploit automation, no unauthorized scanning."],
  ["Provider Live", "/provider-live", "Etherscan/GoPlus/GitHub/advisory provider readiness and error handling."],
  ["Worker Execution", "/worker-execution", "Slither, Semgrep, Foundry, Echidna, and Mythril worker status."],
  ["Launch Validation", "/launch-validation", "Phase 31 compression, payment readiness, Slither readiness, and dependency intelligence."],
  ["Pilot Experience", "/pilot-experience", "Phase 35 first-user journey cleanup, clearer setup states, feedback intake, and safe copy checks."],
  ["MVP Launch Pack", "/launch-pack", "Phase 36 first 10 users tracker, outreach kit, public beta checklist, and safe launch claim guardrails."],
  ["Launch Final QA", "/launch-final", "Final release gates for Vercel, Render, Supabase, Razorpay, SEO, and legal ops."],
  ["Trust Metrics", "/trust-metrics", "Public-safe metrics, advisory mapping, disclosures, and no fake discovery claims."],
];

export const metadata = {
  title: "Docs | Web3Guard AI",
  description: "Web3Guard methodology, limitations, responsible use, provider setup, and launch validation docs.",
};

export default function DocsPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Docs</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Advanced pages moved out of the main journey.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Public navigation stays simple. Technical layers remain available here for setup, transparency, and advanced review.
        </p>
      </section>
      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {docs.map(([title, href, text]) => (
          <Link key={href} href={href} className="glass-tile block p-5 transition hover:-translate-y-1">
            <p className="text-lg font-black text-white">{title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
            <p className="mt-4 text-xs font-bold text-cyan">Open →</p>
          </Link>
        ))}
      </section>
    </main>
  );
}
