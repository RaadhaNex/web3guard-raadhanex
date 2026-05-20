import Link from "next/link";

const docGroups = [
  {
    title: "Start here",
    text: "Use these pages to understand what Web3Guard checks and what it never claims.",
    links: [
      ["Methodology", "/methodology", "How evidence, confidence, and Not Assessed states are handled."],
      ["Limitations", "/limitations", "Where professional security review is still required."],
      ["Responsible use", "/responsible-use", "No private keys, no wallet signing, no exploit automation, no unauthorized scanning."],
    ],
  },
  {
    title: "Report and payment",
    text: "Use these when a founder wants a clean report path or paid pilot flow.",
    links: [
      ["Report center", "/report", "Convert scan evidence into a pre-audit readiness report path."],
      ["Scope & refund", "/scope-refund", "Keep paid pilot-review scope clear and fair."],
      ["Payment validation", "/payment-validation", "Check Razorpay/UPI verification states before treating a payment as complete."],
    ],
  },
  {
    title: "Setup and advanced",
    text: "Use only when enabling provider keys, workers, or deeper tooling.",
    links: [
      ["Provider live", "/provider-live", "Explorer, advisory, GitHub, and external-provider states."],
      ["Worker execution", "/worker-execution", "Slither, Semgrep, Mythril, and worker-required boundaries."],
      ["Advanced tools", "/advanced", "All non-core screens organized in one simple More hub."],
    ],
  },
];

const quickRules = [
  "Pre-audit readiness only",
  "Not a certified audit",
  "No security guarantee",
  "Unavailable tools stay visible",
];

export const metadata = {
  title: "Docs | Web3Guard AI",
  description: "Simple Web3Guard docs for methodology, limitations, payment validation, provider setup, and responsible use.",
};

export default function DocsPage() {
  return (
    <main className="docs-final-page mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="docs-final-hero scroll-motion-ready">
        <div>
          <p className="video-section-kicker">Docs</p>
          <h1>Clear docs, no confusing beta clutter.</h1>
          <p>
            These pages explain what Web3Guard is useful for, where evidence comes from, and what must stay manual or not assessed.
          </p>
        </div>
        <div className="docs-rule-card">
          {quickRules.map((rule) => (
            <span key={rule}>{rule}</span>
          ))}
        </div>
      </section>

      <section className="docs-group-grid mt-8">
        {docGroups.map((group) => (
          <article key={group.title} className="docs-group-card scroll-motion-ready">
            <h2>{group.title}</h2>
            <p>{group.text}</p>
            <div className="docs-link-stack">
              {group.links.map(([label, href, text]) => (
                <Link key={href} href={href} className="docs-link-card">
                  <b>{label}</b>
                  <small>{text}</small>
                  <span>Open →</span>
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
