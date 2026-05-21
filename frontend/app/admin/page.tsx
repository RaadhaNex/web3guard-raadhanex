import Link from "next/link";

export const metadata = {
  title: "Admin Operations | Web3Guard AI",
  description: "Separated internal operations hub for Web3Guard AI reviewer, payment, lead, and super-admin workflows.",
  robots: { index: false, follow: false },
};

const adminModules = [
  {
    title: "Reviewer Onboarding",
    href: "/admin/reviewers",
    badge: "Phase R",
    text: "Reviewer identity, NDA, conflict, sample-review, and quality gates for human-reviewed delivery.",
  },
  {
    title: "Professional Monitoring",
    href: "/professional/monitoring",
    badge: "Phase N",
    text: "Post-review baselines, drift events, acknowledgements, and continuous assurance readiness.",
  },
  {
    title: "Professional Integrations",
    href: "/professional/integrations",
    badge: "Phase O/P",
    text: "GitHub and on-chain webhook setup with real evidence-only event ingestion.",
  },
  {
    title: "Formal/Fuzz Worker",
    href: "/professional/worker",
    badge: "Phase Q",
    text: "Foundry/Echidna runner console that stays disabled until explicit isolated-worker configuration.",
  },
  {
    title: "Reviewer Workbench",
    href: "/admin/reviewer",
    badge: "Phase M",
    text: "Assignments, fix verification, report readiness, reviewed approval, and public-proof handoff.",
  },
  {
    title: "Leads",
    href: "/admin/leads",
    badge: "Revenue ops",
    text: "Lead queue, UPI references, manual payment verification, and reviewer assignment context.",
  },
  {
    title: "Payments",
    href: "/admin/payments",
    badge: "Billing ops",
    text: "Payment and subscription records. No fake payment success without backend verification.",
  },
  {
    title: "Super Panel",
    href: "/admin/super",
    badge: "Internal",
    text: "System health, feature flags, audit log, and admin-only operational controls.",
  },
  {
    title: "Public Proof UI",
    href: "/report/proof",
    badge: "Trust ops",
    text: "Draft, approve, publish, verify, and revoke evidence-first public proof packets.",
  },
  {
    title: "Report Verifier",
    href: "/report/verify",
    badge: "Public trust",
    text: "Verify report hashes and proof integrity without claiming certified audit status.",
  },
];

export default function AdminOperationsPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="glass-tile p-6 sm:p-8">
        <p className="section-label">Admin Operations</p>
        <h1 className="mt-3 text-4xl font-black tracking-[-0.06em] sm:text-6xl">Separated internal control hub.</h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400">
          Admin workflows stay separate from public product pages. Use these tools only for internal operations, real reviewer workflows, manual payment checks, and proof/report governance.
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          <span className="badge badge-green">Internal only</span>
          <span className="badge badge-amber">No certified-audit claim</span>
          <span className="badge badge-cyan">Real records only</span>
          <span className="badge badge-purple">Admin token where backend requires it</span>
        </div>
      </section>

      <section className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {adminModules.map((module) => (
          <Link key={module.href} href={module.href} className="glass-tile group block p-5 transition hover:-translate-y-1 hover:border-cyan/25">
            <div className="flex items-start justify-between gap-3">
              <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 font-mono text-cyan">AD</div>
              <span className="badge badge-cyan">{module.badge}</span>
            </div>
            <h2 className="mt-4 text-xl font-black text-white">{module.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{module.text}</p>
            <p className="mt-5 text-sm font-bold text-cyan opacity-80 transition group-hover:translate-x-1 group-hover:opacity-100">Open module →</p>
          </Link>
        ))}
      </section>

      <section className="mt-8 rounded-[1.5rem] border border-amber-400/20 bg-amber-500/10 p-5 text-sm leading-7 text-amber-100">
        <b>Boundary:</b> This hub improves operations only. Certified audit status still requires real legal scope, qualified human reviewers, signed delivery process, and external trust evidence.
      </section>
    </main>
  );
}
