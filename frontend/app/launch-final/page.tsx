import { LaunchFinalClient } from "@/components/launch-final/LaunchFinalClient";

export default function LaunchFinalPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="quantum-stage p-6 sm:p-8">
        <p className="section-label">Phase 30 · Launch final QA + public release</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-6xl">
          Final public-release gate without fake launch claims.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Phase 30 gives RAADHANEX a safe launch command center: release gates, production checklist, deploy verification, safe release notes, and blocked wording checks before public beta traffic.
        </p>
      </section>
      <LaunchFinalClient />
    </main>
  );
}
