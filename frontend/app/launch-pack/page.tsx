import Link from "next/link";
import { MvpLaunchPackClient } from "@/components/launch-pack/MvpLaunchPackClient";

export const metadata = {
  title: "MVP Launch Pack | Web3Guard AI",
  description: "MVP launch pack MVP launch pack, first 10 users tracker, honest outreach kit, public beta checklist, and safe claim guardrails.",
};

export default function LaunchPackPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">MVP launch pack</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">MVP launch pack for the first 10 real users.</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          This is the final build-phase sprint. Stop adding random pages, apply all patches, test, deploy, validate Razorpay/worker/provider truth states, and get 10 real founder sessions before the next roadmap.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Run scanner →</Link>
          <Link href="/report/pilot" className="btn-secondary">Pilot report</Link>
          <Link href="/pilot-experience" className="btn-secondary">Pilot UX</Link>
        </div>
      </section>
      <MvpLaunchPackClient />
    </main>
  );
}
