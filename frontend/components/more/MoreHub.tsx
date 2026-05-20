import Link from "next/link";

const groups = [
  {
    title: "Core output",
    note: "Use these after scanning.",
    items: [
      ["Results", "/results", "Read assessed, missing, tool, API-key, and manual-review states."],
      ["Report", "/report", "Prepare the clean founder readiness report path."],
      ["Saved scans", "/dashboard/scans", "Open previous work when login/storage are configured."],
    ],
  },
  {
    title: "Trust and help",
    note: "Use these to understand the beta.",
    items: [
      ["Docs", "/docs", "Methodology, limitations, responsible use, and setup pages."],
      ["Feature status", "/feature-status", "See what is live, beta, manual, or setup-required."],
      ["Risk intelligence", "/risk-intelligence", "Explain impact, likely risk, fix path, and verification."],
    ],
  },
  {
    title: "Scanner surfaces",
    note: "Use these for direct surface checks.",
    items: [
      ["Website", "/scanner/website", "HTTPS, headers, policy pages, and launch surface."],
      ["Smart contract", "/scanner/contract", "Contract evidence and static-analysis readiness."],
      ["API", "/scanner/api-deep", "Auth, CORS, webhook, rate-limit, and admin exposure."],
      ["Wallet UX", "/scanner/wallet", "Wallet-connect and transaction-flow safety review."],
      ["GitHub", "/scanner/github", "Repo hygiene, packages, CI, and exposure signals."],
      ["Admin OpSec", "/scanner/admin-opsec", "MFA, roles, multisig, and incident-response evidence."],
    ],
  },
  {
    title: "Setup / internal",
    note: "Keep these away from the main user path.",
    items: [
      ["Worker execution", "/worker-execution", "Slither/Semgrep/tool-worker execution states."],
      ["Provider live", "/provider-live", "Explorer, advisory, GitHub, and external provider states."],
      ["Payment validation", "/payment-validation", "Razorpay/UPI verification for the ₹999 pilot flow."],
      ["Trust metrics", "/trust-metrics", "Public-safe metrics without fake audit claims."],
    ],
  },
];

export function MoreHub() {
  return (
    <main className="more-hub-page mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/70 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-200/80">More</p>
        <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">All extra screens, cleaned and grouped.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
          Main flow stays simple: Home → Scan → Results → Report → Price. Everything else lives here with a clear use case.
        </p>
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        {groups.map((group) => (
          <article key={group.title} className="rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
            <h2 className="text-2xl font-black text-white">{group.title}</h2>
            <p className="mt-2 text-sm text-slate-400">{group.note}</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {group.items.map(([label, href, text]) => (
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
