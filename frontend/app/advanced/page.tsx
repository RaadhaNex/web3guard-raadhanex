import Link from "next/link";

const featureGroups = [
  {
    title: "User flow",
    note: "Useful for normal users after they run a scan.",
    items: [
      ["Results", "/results", "See what was assessed, what is missing, and what needs manual review."],
      ["Report center", "/report", "Create a founder-friendly readiness report path."],
      ["Saved scans", "/dashboard/scans", "Return to previous scans when login/storage is configured."],
    ],
  },
  {
    title: "Trust and learning",
    note: "Useful for understanding the beta before paying or sharing reports.",
    items: [
      ["Docs", "/docs", "Methodology, limitations, responsible use, and setup guides."],
      ["Feature status", "/feature-status", "See live, beta, setup-required, and manual states."],
      ["Risk intelligence", "/risk-intelligence", "Understand impact, likely risk, fix path, and verification steps."],
    ],
  },
  {
    title: "Scanner engines",
    note: "Useful when you want to check one surface directly.",
    items: [
      ["Website surface", "/scanner/website", "HTTPS, headers, robots, sitemap, and policy-page readiness."],
      ["Smart contract", "/scanner/contract", "Solidity rules and supplied contract evidence."],
      ["API readiness", "/scanner/api-deep", "Auth, CORS, webhook, rate-limit, and admin-route review."],
      ["Wallet flow", "/scanner/wallet", "Approval, chain mismatch, blind signing, and transaction preview readiness."],
      ["GitHub repo", "/scanner/github", "Repo hygiene, package metadata, CI, and secret-exposure patterns."],
      ["Admin OpSec", "/scanner/admin-opsec", "MFA, multisig, timelock, role separation, and incident response evidence."],
    ],
  },
  {
    title: "Setup / internal",
    note: "Keep these away from the main user path unless you are configuring the product.",
    items: [
      ["Worker execution", "/worker-execution", "Real tool execution states for Slither, Semgrep, and worker-required tools."],
      ["Provider live", "/provider-live", "Explorer, advisory, GitHub, and external-provider configuration state."],
      ["Payment validation", "/payment-validation", "Razorpay/UPI test and verification workflow for the ₹999 pilot path."],
      ["Trust metrics", "/trust-metrics", "Public-safe metrics without fake discovery or audit claims."],
      ["Launch pack", "/launch-pack", "Checklist and outreach support after the core product flow is stable."],
      ["Community review", "/community-review", "Optional review workflow for later public-beta growth."],
    ],
  },
];

export const metadata = {
  title: "More Tools | Web3Guard AI",
  description: "Clean More hub for Web3Guard results, reports, docs, scanner engines, and advanced setup screens.",
};

export default function AdvancedToolsPage() {
  return (
    <main className="more-hub-page mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="more-hub-hero scroll-motion-ready">
        <p className="video-section-kicker">More</p>
        <h1>Everything outside the main flow, organized clearly.</h1>
        <p>
          Normal users should understand each screen in seconds. Core flow stays simple: Home → Scan → Results → Report → Price.
        </p>
      </section>

      <section className="more-hub-grid mt-8">
        {featureGroups.map((group) => (
          <article key={group.title} className="more-hub-group scroll-motion-ready">
            <div className="more-hub-group-head">
              <h2>{group.title}</h2>
              <p>{group.note}</p>
            </div>
            <div className="more-hub-links">
              {group.items.map(([label, href, text]) => (
                <Link key={href} href={href} className="more-hub-link">
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
