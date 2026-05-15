import { UpiCheckout } from "@/components/checkout/UpiCheckout";
import type { PackagePlan } from "@/lib/types";

const plans: PackagePlan[] = [
  { id: "free-scan", name: "Free Scan", category: "free", price_inr: 0, description: "Instant basic scan and score preview.", deliverables: ["Scanner access", "Basic score", "Top risk hints"], turnaround_time: "Instant", cta: "Start Free", billing_cycles: ["one_time"] },
  { id: "quick-risk-report", name: "Quick Risk Scan Report", category: "service", price_inr: 999, description: "Manual review of scan output with priority fixes.", deliverables: ["Priority risks", "Founder summary", "Fix direction"], turnaround_time: "24-48 hours", cta: "Request Report", billing_cycles: ["one_time"] },
  { id: "detailed-launch-readiness", name: "Detailed Launch Readiness", category: "service", price_inr: 2999, description: "Contract + website + dApp + API + wallet + admin readiness.", deliverables: ["Multi-surface review", "Report", "Before-launch checklist"], turnaround_time: "2-4 days", cta: "Request Detail", billing_cycles: ["one_time"], popular: true },
  { id: "fix-suggestion-pack", name: "Fix Suggestion Pack", category: "service", price_inr: 7999, description: "Fix guidance, safer patterns, and test checklist.", deliverables: ["Fix guidance", "Test checklist", "Follow-up scan"], turnaround_time: "3-5 days", cta: "Request Fix Pack", billing_cycles: ["one_time"] },
  { id: "manual-pre-audit", name: "Manual Pre-Audit Review", category: "service", price_inr: 14999, description: "Manual pre-audit package for serious launches.", deliverables: ["Manual review", "Scope notes", "Risk matrix"], turnaround_time: "5-7 days", cta: "Request Manual", billing_cycles: ["one_time"] },
  { id: "full-launch-readiness", name: "Full Launch Readiness Review", category: "service", price_inr: 29999, description: "Full multi-surface readiness review.", deliverables: ["Complete report", "OpSec review", "Final checklist"], turnaround_time: "7-10 days", cta: "Request Full", billing_cycles: ["one_time"] },
  { id: "builder-monthly", name: "Builder Monthly Subscription", category: "subscription", price_inr: 2999, description: "Monthly plan for freelancers/agencies with repeated scans.", deliverables: ["20 scans/month", "5 report drafts", "Priority follow-up"], turnaround_time: "Monthly", cta: "Pay Monthly", billing_cycles: ["monthly"], popular: true },
  { id: "shield-monthly", name: "Shield Monthly Subscription", category: "subscription", price_inr: 9999, description: "Higher-touch monthly readiness support for startups.", deliverables: ["More report reviews", "2 readiness calls", "Admin/Wallet review"], turnaround_time: "Monthly", cta: "Pay Shield", billing_cycles: ["monthly"] }
];

export function PricingSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Razorpay + UPI manual fallback</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Verified payments and subscriptions in one funnel.</h2>
          <p className="mt-3 max-w-2xl text-slate-400">Phase 8 supports real Razorpay order/signature verification when keys are configured, while preserving UPI manual fallback for users who want to pay by any UPI app.</p>
        </div>
        <a href="/contact" className="btn-secondary">Submit Review Request</a>
      </div>
      <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {plans.map((plan) => (
          <div key={plan.id} className={`card flex flex-col p-6 ${plan.popular ? "border-cyan/40" : ""}`}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-xl font-black">{plan.name}</p>
              {plan.popular && <span className="rounded-full bg-cyan/15 px-3 py-1 text-xs font-bold text-cyan">Popular</span>}
            </div>
            <p className="mt-3 text-4xl font-black">₹{plan.price_inr.toLocaleString("en-IN")}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">{plan.category}</p>
            <p className="mt-3 text-sm leading-6 text-slate-400">{plan.description}</p>
            <ul className="mt-4 flex-1 space-y-2 text-sm text-slate-300">
              {plan.deliverables.map((item) => <li key={item}>✓ {item}</li>)}
            </ul>
            <p className="mt-4 text-xs text-slate-500">Turnaround: {plan.turnaround_time}</p>
            <UpiCheckout plan={plan} />
          </div>
        ))}
      </div>
    </section>
  );
}
