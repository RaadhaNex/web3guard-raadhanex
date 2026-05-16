import Link from "next/link";
import { LeadForm } from "@/components/scanner/LeadForm";

export default function ContactPage() {
  return (
    <div className="mx-auto grid max-w-7xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.8fr_1.2fr] lg:px-8">
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Request review</p>
        <h1 className="mt-3 text-4xl font-black sm:text-5xl">Submit project for paid Web3 launch readiness review.</h1>
        <p className="mt-4 text-slate-400">
          Create a payment intent on pricing page. If Razorpay is configured, Checkout verification can confirm payment; if using UPI manual fallback, paste the transaction/reference ID here. You can also submit first and pay later.
        </p>
        <div className="mt-6 rounded-2xl border border-cyan/20 bg-cyan/10 p-4 text-sm leading-6 text-cyan-50">
          keeps trust boundaries clear: paid review starts only after Razorpay backend verification or manual admin payment confirmation, and no certified audit claim is made.
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <Link href="/pricing" className="btn-primary">Create Payment Intent</Link>
          <Link href="/scope-refund" className="btn-secondary">Read Scope Policy</Link>
        </div>
      </div>
      <LeadForm />
    </div>
  );
}
