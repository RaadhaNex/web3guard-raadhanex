import Link from "next/link";
import { PilotExperienceClient } from "@/components/pilot-experience/PilotExperienceClient";

export const metadata = {
  title: "Pilot Experience | Web3Guard AI",
  description: "Phase 35 pilot user experience polish, status copy, feedback intake, and safe claim checks.",
};

export default function PilotExperiencePage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Phase 35</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">Pilot user experience polish without adding clutter.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Phase 35 keeps the public journey simple, hides advanced pages from first-time users, improves setup-state wording, and collects pilot feedback without private keys or fake claims.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Start the 7-step journey →</Link>
          <Link href="/results" className="btn-secondary">Review result engine</Link>
          <Link href="/payment-validation" className="btn-secondary">Payment validation</Link>
        </div>
      </section>
      <PilotExperienceClient />
    </main>
  );
}
