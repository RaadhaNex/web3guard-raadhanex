import Link from "next/link";

const plans = [
  {
    name: "Free Scan",
    badge: "Start here",
    price: "₹0",
    description: "Run a first readiness scan and see what is assessed, missing, or manual.",
    cta: "Start scan",
    href: "/scanner/unified-url",
    featured: false,
    features: ["URL-based readiness input", "Assessed / Not Assessed states", "No fake pass or fake score", "Pre-audit only"],
  },
  {
    name: "Pilot Report",
    badge: "Most useful",
    price: "₹999",
    description: "A founder-friendly report path for early beta users after scan evidence is ready.",
    cta: "Open ₹999 flow",
    href: "/payment-validation",
    featured: true,
    features: ["Evidence summary", "Priority fix checklist", "Clear limitations", "Payment verification required"],
  },
  {
    name: "Manual Review",
    badge: "Scoped",
    price: "Custom",
    description: "For teams that need human review, provider setup, or launch-readiness support.",
    cta: "Request scope",
    href: "/contact",
    featured: false,
    features: ["Manual evidence triage", "Tool/provider setup guidance", "Report cleanup", "No certified-audit claim"],
  },
];

export function PricingSection() {
  return (
    <main className="pricing-final-page mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="pricing-clean-head">
        <span className="pricing-clean-chip">Free scan</span>
        <span className="pricing-clean-chip">₹999 pilot path</span>
        <span className="pricing-clean-chip">Manual review</span>
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-3" aria-label="Pricing plans">
        {plans.map((plan) => (
          <article
            key={plan.name}
            className={`relative overflow-hidden rounded-[1.7rem] border p-5 shadow-2xl sm:p-6 ${
              plan.featured
                ? "border-cyan-300/30 bg-cyan-300/[0.07] shadow-cyan-950/30"
                : "border-white/10 bg-white/[0.035] shadow-black/20"
            }`}
          >
            <div className="pointer-events-none absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-cyan-300/10 to-transparent" />
            <div className="relative flex items-center justify-between gap-3">
              <span className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1 text-[0.65rem] font-black uppercase tracking-[0.16em] text-slate-200">
                {plan.badge}
              </span>
              {plan.featured ? <span className="rounded-full bg-cyan-300/15 px-3 py-1 text-[0.65rem] font-black uppercase tracking-[0.16em] text-cyan-100">Recommended</span> : null}
            </div>
            <h2 className="relative mt-5 text-2xl font-black text-white">{plan.name}</h2>
            <p className="relative mt-3 text-sm leading-7 text-slate-300">{plan.description}</p>
            <strong className="relative mt-6 block text-5xl font-black tracking-[-0.07em] text-white">{plan.price}</strong>
            <ul className="relative mt-6 grid gap-3 text-sm text-slate-300">
              {plan.features.map((feature) => (
                <li key={feature} className="flex gap-2">
                  <span className="mt-1 h-2 w-2 rounded-full bg-cyan-300" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
            <Link
              href={plan.href}
              className={`relative mt-7 inline-flex w-full items-center justify-center rounded-full px-5 py-3 text-sm font-black transition hover:-translate-y-0.5 ${
                plan.featured ? "bg-cyan-200 text-slate-950" : "border border-white/10 bg-white/[0.06] text-white"
              }`}
            >
              {plan.cta} →
            </Link>
          </article>
        ))}
      </section>
    </main>
  );
}
