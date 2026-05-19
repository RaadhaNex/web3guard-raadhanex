import Link from "next/link";

const plans = [
  {
    name: "Free",
    badge: "Live Now",
    tone: "green",
    price: "₹0 Free Forever",
    description: "Instant launch-surface scan, split confidence scores, evidence gaps, and direct export.",
    cta: "Start Free Scan →",
    href: "/scanner/unified-url",
    live: true,
    features: ["Unified URL scanner", "Solidity rule hints", "PDF / HTML / MD / JSON export", "Free tools and checklists", "Not Assessed transparency"],
  },
  {
    name: "Builder",
    badge: "Coming Soon",
    tone: "amber",
    price: "₹999/mo",
    description: "Planned workflow for saved scans, deeper evidence packs, and founder-friendly triage.",
    cta: "Notify Me",
    href: "/contact",
    live: false,
    features: ["Saved scan upgrades", "Manual review request", "Evidence pack assistant", "Priority fix checklist", "Payment activation after final phase"],
  },
  {
    name: "Pro",
    badge: "Coming Soon",
    tone: "amber",
    price: "Custom",
    description: "Planned support for teams preparing audits, contests, bug bounties, and post-launch monitoring.",
    cta: "Request Scope",
    href: "/contact",
    live: false,
    features: ["Pre-audit pack review", "Bug bounty readiness", "CI security workflow", "External-tool setup support", "No certified-audit claim"],
  },
];

export function PricingSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="section-label">Pricing</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Start free. Paid plans stay locked until verified.</h2>
          <p className="mt-3 max-w-xl text-sm leading-7 text-slate-400">
            The public beta scan is live now. Paid tiers are roadmap cards only until Razorpay/UPI order, verification, webhook, and audit logs are implemented.
          </p>
        </div>
        <Link href="/limitations" className="btn-secondary shrink-0">See limitations →</Link>
      </div>

      <div className="mt-10 grid gap-4 lg:grid-cols-3">
        {plans.map((plan) => (
          <div key={plan.name} className={`card flex flex-col p-6 ${plan.live ? "card-glow" : "opacity-75"}`}>
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-xl font-black text-white">{plan.name}</h3>
              <span className={plan.tone === "green" ? "badge badge-green" : "badge badge-amber"}>{plan.badge}</span>
            </div>

            <div className="mt-5">
              <p className={`text-4xl font-black tracking-tight ${plan.live ? "text-cyan" : "text-slate-300 line-through decoration-slate-600/70"}`}>
                {plan.price}
              </p>
              <p className="mt-3 text-sm leading-6 text-slate-400">{plan.description}</p>
            </div>

            <ul className="mt-6 flex-1 space-y-3">
              {plan.features.map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm leading-5 text-slate-300">
                  <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full border border-emerald-400/20 bg-emerald-400/10 text-[10px] font-black text-emerald-300">✓</span>
                  {item}
                </li>
              ))}
            </ul>

            <Link href={plan.href} className={plan.live ? "btn-primary mt-7" : "btn-secondary mt-7"}>
              {plan.cta}
            </Link>
          </div>
        ))}
      </div>

      <p className="mt-8 text-center text-xs text-slate-500">
        Pre-audit only · Not a certified audit · <Link href="/limitations" className="text-cyan hover:underline">See limitations</Link>
      </p>
    </section>
  );
}
