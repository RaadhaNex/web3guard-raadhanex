import Link from "next/link";

const plans = [
  {
    name: "Free Readiness Scan",
    badge: "Live beta",
    tone: "green",
    price: "₹0",
    subprice: "Free public beta",
    description: "Best first step for founders who want to understand launch-surface gaps before spending on manual review.",
    cta: "Start free scan →",
    href: "/scanner/unified-url",
    live: true,
    features: [
      "Unified launch readiness scan",
      "Assessed vs Not Assessed separation",
      "Basic fix priorities",
      "Report export when payload is available",
      "No private key or wallet signing",
    ],
  },
  {
    name: "Pilot Readiness Report",
    badge: "Validate before sale",
    tone: "cyan",
    price: "₹999",
    subprice: "Per pilot report",
    description: "Clear early-user offer for a founder-ready pre-audit report. Access must unlock only after verified Razorpay/UPI payment.",
    cta: "Validate ₹999 flow",
    href: "/payment-validation",
    live: true,
    features: [
      "Founder-ready report workflow",
      "Evidence summary and limitations",
      "Priority fix checklist",
      "Payment must be backend-verified",
      "Not a certified audit",
    ],
  },
  {
    name: "Manual / Pro Review",
    badge: "Scope manually",
    tone: "amber",
    price: "Custom",
    subprice: "After scope review",
    description: "For teams that need deeper manual review, audit preparation, provider setup, or post-scan launch support.",
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
    <section className="cinematic-section mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="section-label">Plans</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Simple pricing for the first 10 beta users.</h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-400">
            Keep the user journey simple: free scan, review results, then offer the ₹999 pilot readiness report only when payment validation is live. Missing providers and missing tools remain visible.
          </p>
        </div>
        <Link href="/limitations" className="btn-secondary shrink-0">See limitations →</Link>
      </div>

      <div className="mt-10 grid gap-4 lg:grid-cols-3">
        {plans.map((plan) => (
          <div key={plan.name} className={`card cinematic-card flex flex-col p-6 ${plan.live ? "card-glow" : "opacity-80"}`}>
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-xl font-black text-white">{plan.name}</h3>
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

      <div className="mt-8 rounded-2xl border border-amber-300/15 bg-amber-300/[0.055] p-4 text-center text-xs leading-6 text-amber-100/85">
        Pre-audit readiness only · Not a certified audit · No security guarantee · No fake payment success ·{" "}
        <Link href="/limitations" className="font-bold text-amber-50 hover:underline">See limitations</Link>
      </div>
    </section>
  );
}
