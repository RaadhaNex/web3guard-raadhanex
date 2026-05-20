import Link from "next/link";

const plans = [
  {
    name: "Free Readiness Scan",
    badge: "Live beta",
    tone: "green",
    price: "₹0",
    subprice: "Free public beta",
    description: "Quick launch readiness scan for founders who want to see visible website, dApp, API, wallet, and launch-surface gaps.",
    cta: "Start free scan →",
    href: "/scanner/unified-url",
    live: true,
    features: [
      "Unified readiness scan",
      "Assessed vs Not Assessed split",
      "Basic launch priorities",
      "Export when scan data exists",
      "No private key or wallet signing",
    ],
  },
  {
    name: "Pilot Readiness Report",
    badge: "Verified flow",
    tone: "cyan",
    price: "₹999",
    subprice: "Per pilot report",
    description: "Founder-ready pre-audit report path for early users. Access should unlock only after backend-verified payment.",
    cta: "Validate ₹999 flow",
    href: "/payment-validation",
    live: true,
    features: [
      "Evidence summary",
      "Limitations clearly shown",
      "Priority fix checklist",
      "Payment verification required",
      "Not a certified audit",
    ],
  },
  {
    name: "Manual / Pro Review",
    badge: "Scoped manually",
    tone: "amber",
    price: "Custom",
    subprice: "After scope review",
    description: "For teams that need manual evidence review, audit preparation, provider setup, or post-scan launch support.",
    cta: "Request scope",
    href: "/contact",
    live: false,
    features: [
      "Manual evidence triage",
      "Pre-audit pack review",
      "Provider/tool setup support",
      "Bug bounty readiness planning",
      "No audit-company claim",
    ],
  },
];

function badgeClass(tone: string) {
  if (tone === "green") return "badge badge-green";
  if (tone === "cyan") return "badge badge-cyan";
  return "badge badge-amber";
}

export function PricingSection() {
  return (
    <section className="cinematic-section mx-auto max-w-7xl px-4 py-14 sm:px-6 sm:py-18 lg:px-8">
      <div className="grid gap-4 lg:grid-cols-3">
        {plans.map((plan) => (
          <div key={plan.name} className={`card cinematic-card flex flex-col p-6 ${plan.live ? "card-glow" : "opacity-85"}`}>
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-xl font-black text-white">{plan.name}</h2>
              <span className={badgeClass(plan.tone)}>{plan.badge}</span>
            </div>

            <div className="mt-5">
              <p className={`text-4xl font-black tracking-tight ${plan.live ? "text-cyan" : "text-slate-300"}`}>
                {plan.price}
              </p>
              <p className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-slate-500">{plan.subprice}</p>
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
    </section>
  );
}
