import Link from "next/link";

const groups = [
  {
    title: "Worker and provider setup",
    text: "Use these only when you are ready to enable real scanner tools or external APIs.",
    links: [
      ["Scanner depth", "/scanner-depth"],
      ["Risk intelligence", "/risk-intelligence"],
      ["Worker runs", "/worker-runs"],
      ["Worker execution", "/worker-execution"],
      ["Provider live", "/provider-live"],
      ["Provider readiness", "/provider-readiness"],
    ],
  },
  {
    title: "Trust and monitoring",
    text: "Advanced pages for passports, monitoring, public trust artifacts, and advisory tracking.",
    links: [
      ["Security passport", "/security-passport"],
      ["Trust metrics", "/trust-metrics"],
      ["Continuous monitoring", "/continuous-monitoring"],
      ["Trust pages", "/trust-pages"],
    ],
  },
  {
    title: "Launch and agency ops",
    text: "Use after the core scanner/report flow is validated with real users.",
    links: [
      ["Launch final", "/launch-final"],
      ["MVP launch pack", "/launch-pack"],
      ["Agency launch", "/agency-launch"],
      ["Community review", "/community-review"],
    ],
  },
];

export default function AdvancedToolsPage() {
  return (
    <main className="cinematic-page-shell mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="cinematic-page-hero clean-panel cinematic-panel p-6 sm:p-8">
        <p className="section-label">More / Advanced tools</p>
        <h1 className="mt-3 max-w-3xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Hidden from main navigation, still available when needed.
        </h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400">
          First users should follow the clean path: Home → Scan → Results → Report → Price. These tools stay here for setup, power users, and internal validation.
        </p>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        {groups.map((group) => (
          <article key={group.title} className="clean-panel cinematic-panel p-6">
            <h2 className="text-xl font-black text-white">{group.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{group.text}</p>
            <div className="mt-5 grid gap-2">
              {group.links.map(([label, href]) => (
                <Link key={href} href={href} className="rounded-xl border border-white/[0.07] bg-white/[0.025] px-4 py-3 text-sm font-bold text-slate-300 transition hover:border-cyan/25 hover:bg-cyan/[0.04] hover:text-white">
                  {label} →
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
