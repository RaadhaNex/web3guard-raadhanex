import { UpiCheckout } from "@/components/checkout/UpiCheckout";
import type { PackagePlan } from "@/lib/types";
import Link from "next/link";

const plans: PackagePlan[] = [
  { id: "free-scan",              name: "Free Scan",                  category: "free",         price_inr: 0,     description: "Instant automated scan with score and top risk indicators.",        deliverables: ["Scanner access", "Risk score", "Top 5 findings"],          turnaround_time: "Instant",    cta: "Start Free",       billing_cycles: ["one_time"] },
  { id: "quick-risk-report",      name: "Quick Risk Report",           category: "service",      price_inr: 999,   description: "Manual review of your scan with prioritised fix guidance.",         deliverables: ["Priority risks", "Founder summary", "Fix direction"],      turnaround_time: "24–48 hrs",  cta: "Get Report",       billing_cycles: ["one_time"] },
  { id: "detailed-launch",        name: "Launch Readiness Report",     category: "service",      price_inr: 2999,  description: "Full review across contract, website, dApp, API, wallet, admin.",  deliverables: ["Multi-surface review", "Full report", "Before-launch checklist"], turnaround_time: "2–4 days",   cta: "Get Full Report",  billing_cycles: ["one_time"], popular: true },
  { id: "fix-suggestion-pack",    name: "Fix Suggestion Pack",         category: "service",      price_inr: 7999,  description: "Specific fix guidance, safer code patterns, and test checklist.",   deliverables: ["Fix per finding", "Code patterns", "Test checklist"],      turnaround_time: "3–5 days",   cta: "Get Fix Pack",     billing_cycles: ["one_time"] },
  { id: "manual-pre-audit",       name: "Manual Pre-Audit Review",     category: "service",      price_inr: 14999, description: "Comprehensive manual review package for serious launches.",         deliverables: ["Manual review", "Scope notes", "Risk matrix"],             turnaround_time: "5–7 days",   cta: "Request Review",   billing_cycles: ["one_time"] },
  { id: "full-launch-readiness",  name: "Full Launch Readiness",       category: "service",      price_inr: 29999, description: "End-to-end multi-surface readiness review for high-stakes launches.",deliverables: ["Complete report", "OpSec audit", "Final checklist"],       turnaround_time: "7–10 days",  cta: "Request Full",     billing_cycles: ["one_time"] },
];

export function PricingSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">

      {/* Header */}
      <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="section-label">Transparent pricing</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">
            Affordable security reviews for every stage.
          </h2>
          <p className="mt-3 max-w-xl text-sm leading-7 text-slate-400">
            Start with a free scan. Upgrade to a paid expert review when you need it. Pay via UPI, Razorpay, or card — GST invoice on request.
          </p>
        </div>
        <Link href="/contact" className="btn-secondary shrink-0">Talk to us →</Link>
      </div>

      {/* Plans */}
      <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`card flex flex-col p-6 transition hover:-translate-y-0.5 ${plan.popular ? "border-cyan/40" : ""}`}
          >
            {/* Top */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="badge text-xs">{plan.category === "free" ? "Free" : "One-time"}</span>
                <h3 className="mt-2 text-base font-black leading-tight text-white">{plan.name}</h3>
              </div>
              {plan.popular && (
                <span className="shrink-0 rounded-full bg-cyan/10 px-2.5 py-1 text-xs font-bold text-cyan border border-cyan/20">Popular</span>
              )}
            </div>

            {/* Price */}
            <div className="mt-4 flex items-baseline gap-1">
              {plan.price_inr === 0 ? (
                <span className="text-4xl font-black text-white">Free</span>
              ) : (
                <>
                  <span className="text-lg font-bold text-slate-400">₹</span>
                  <span className="text-4xl font-black text-white">{plan.price_inr.toLocaleString("en-IN")}</span>
                </>
              )}
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-400">{plan.description}</p>

            {/* Deliverables */}
            <ul className="mt-4 flex-1 space-y-2">
              {plan.deliverables.map((item) => (
                <li key={item} className="flex items-center gap-2 text-sm text-slate-300">
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none" className="shrink-0">
                    <circle cx="6.5" cy="6.5" r="6" stroke="#22d3ee" strokeOpacity="0.35"/>
                    <path d="M4 6.5l1.8 1.8 3.2-3.2" stroke="#22d3ee" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  {item}
                </li>
              ))}
            </ul>

            <p className="mt-4 text-xs font-medium uppercase tracking-wider text-slate-500">
              Turnaround: {plan.turnaround_time}
            </p>

            <div className="mt-4">
              <UpiCheckout plan={plan} />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-8 text-center text-xs text-slate-500">
        Payments verified manually before review delivery. GST invoice available on request.{" "}
        <Link href="/scope-refund" className="underline hover:text-slate-300">Refund & scope policy</Link>
      </p>
    </section>
  );
}
