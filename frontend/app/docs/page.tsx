import Link from "next/link";

const groups = [
  {
    title: "Start here",
    text: "Understand what Web3Guard checks, what it cannot check, and how to use it safely.",
    links: [
      ["Methodology", "/methodology", "How evidence and states are separated."],
      ["Limitations", "/limitations", "What still needs professional review."],
      ["Responsible use", "/responsible-use", "No keys, no signing, no exploit automation."],
    ],
  },
  {
    title: "Scan and report",
    text: "Pages useful after a founder submits a project URL or evidence.",
    links: [
      ["Scanner", "/scanner/unified-url", "Start the readiness input flow."],
      ["Results", "/results", "See assessed, missing, and manual states."],
      ["Report", "/report", "Prepare a founder-ready report path."],
    ],
  },
  {
    title: "Setup",
    text: "Use these only when enabling real providers, workers, or payment checks.",
    links: [
      ["Feature status", "/feature-status", "Live, beta, manual, and setup states."],
      ["Advanced tools", "/advanced", "All non-core tools in one hub."],
      ["Payment validation", "/payment-validation", "Razorpay/UPI verification state."],
    ],
  },
];

export const metadata = {
  title: "Docs | Web3Guard AI",
  description: "Simple docs for Web3Guard AI methodology, limitations, reports, providers, and responsible use.",
};

export default function DocsPage() {
  return (
    <main className="docs-final-page mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="docs-clean-head">
        <span className="pricing-clean-chip">Methodology</span>
        <span className="pricing-clean-chip">Limitations</span>
        <span className="pricing-clean-chip">Responsible use</span>
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        {groups.map((group) => (
          <article key={group.title} className="rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
            <h2 className="text-2xl font-black text-white">{group.title}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-300">{group.text}</p>
            <div className="mt-5 grid gap-3">
              {group.links.map(([label, href, text]) => (
                <Link key={href} href={href} className="rounded-2xl border border-white/10 bg-slate-950/45 p-4 transition hover:border-cyan-300/30 hover:bg-cyan-300/[0.05]">
                  <b className="block text-white">{label}</b>
                  <small className="mt-1 block text-sm leading-6 text-slate-400">{text}</small>
                  <span className="mt-2 block text-xs font-black uppercase tracking-[0.16em] text-cyan-200">Open →</span>
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
