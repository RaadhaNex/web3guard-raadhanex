import Link from "next/link";

const plans = [
  {
    name: "Free Readiness Scan",
    badge: "Start here",
    price: "₹0",
    subprice: "Public beta scan",
    description: "A clean first scan for Web3 founders who want to see visible launch gaps before paying for deeper review.",
    cta: "Start free scan",
    href: "/scanner/unified-url",
    featured: false,
    features: [
      "Website, dApp, API, wallet, GitHub, and admin evidence inputs",
      "Assessed vs Not Assessed states",
      "Missing tools stay visible instead of guessed",
      "No private key, seed phrase, wallet signing, or exploit automation",
    ],
  },
  {
    name: "Pilot Readiness Report",
    badge: "Best for first users",
    price: "₹999",
    subprice: "Per pilot report path",
    description: "Founder-friendly pre-audit readiness report flow for early users who need a structured launch checklist.",
    cta: "Open ₹999 flow",
    href: "/payment-validation",
    featured: true,
    features: [
      "Evidence summary and visible coverage gaps",
      "Priority fix checklist for launch decisions",
      "Clear limitations and safe wording",
      "Payment must be backend-verified before access is treated as paid",
    ],
  },
  {
    name: "Manual / Pro Review",
    badge: "Scoped manually",
    price: "Custom",
    subprice: "After scope check",
    description: "For teams that need human review, provider setup, report cleanup, or audit-preparation support.",
    cta: "Request scope",
    href: "/contact",
    featured: false,
    features: [
      "Manual evidence triage",
      "Tool/provider setup support",
      "Pre-audit pack guidance",
      "No certified audit or security guarantee claim",
    ],
  },
];

const compareRows = [
  ["Quick scan", "Included", "Included", "Included"],
  ["Report path", "Preview only", "₹999 pilot", "Scoped"],
  ["Manual reviewer", "No", "Limited by scope", "Yes"],
  ["Certified audit claim", "No", "No", "No"],
];

export function PricingSection() {
  return (
    <section className="pricing-final-page mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="pricing-final-head scroll-motion-ready">
        <p className="video-section-kicker">Pricing</p>
        <h1>Simple pricing for first Web3 founders.</h1>
        <p>
          Start free, then use the ₹999 pilot report path only when the scan evidence is ready. Manual review stays scoped and honest.
        </p>
      </div>

      <div className="pricing-final-grid mt-8">
        {plans.map((plan) => (
          <article key={plan.name} className={`pricing-final-card scroll-motion-ready ${plan.featured ? "pricing-final-card-featured" : ""}`}>
            <div className="pricing-card-glow" />
            <div className="pricing-card-top">
              <span>{plan.badge}</span>
              {plan.featured ? <b>Recommended</b> : null}
            </div>
            <h2>{plan.name}</h2>
            <p className="pricing-card-desc">{plan.description}</p>
            <div className="pricing-card-price">
              <strong>{plan.price}</strong>
              <small>{plan.subprice}</small>
            </div>
            <ul>
              {plan.features.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <Link href={plan.href} className={plan.featured ? "video-hero-primary" : "video-hero-secondary"}>
              {plan.cta} →
            </Link>
          </article>
        ))}
      </div>

      <div className="pricing-compare-panel scroll-motion-ready">
        <div>
          <p className="video-section-kicker">Decision guide</p>
          <h2>Which option should a user choose?</h2>
        </div>
        <div className="pricing-compare-table" role="table" aria-label="Pricing decision guide">
          {compareRows.map(([label, free, pilot, manual]) => (
            <div key={label} className="pricing-compare-row" role="row">
              <strong>{label}</strong>
              <span>{free}</span>
              <span>{pilot}</span>
              <span>{manual}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
