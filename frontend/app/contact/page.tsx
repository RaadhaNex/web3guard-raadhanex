import Link from "next/link";
import { LeadForm } from "@/components/scanner/LeadForm";

export default function ContactPage() {
  return (
    <main className="mx-auto grid max-w-7xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.82fr_1.18fr] lg:px-8">
      <section>
        <p className="section-label">Request scope review</p>
        <h1 className="mt-3 text-4xl font-black sm:text-5xl">Submit your Web3 project for a scoped readiness conversation.</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">
          Share project context, public links, and the type of review you need. Do not paste private keys, seed phrases, production credentials, or customer secrets.
        </p>
        <div className="mt-6 rounded-3xl border border-cyan/20 bg-cyan/10 p-5 text-sm leading-6 text-cyan-50">
          Paid checkout is intentionally deferred. This form is for scope collection and follow-up only; it does not create a payment, subscription, or certified-audit claim.
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <Link href="/scanner/unified-url" className="btn-primary">Run free scan first</Link>
          <Link href="/scope-refund" className="btn-secondary">Read scope policy</Link>
        </div>
        <div className="mt-6 grid gap-3 text-sm text-slate-400">
          {["Authorized projects only", "Pre-audit readiness language", "No wallet signing or secrets", "Manual review scope must be confirmed"].map((item) => (
            <div key={item} className="command-line"><span className="kbd-chip">✓</span><span>{item}</span></div>
          ))}
        </div>
      </section>
      <LeadForm />
    </main>
  );
}
