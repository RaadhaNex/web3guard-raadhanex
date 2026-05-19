import Link from "next/link";

const checks = [
  ["Navigation", "Command palette, header links, footer links, and mobile menu stay visible and readable."],
  ["Scanner UX", "Unified scan remains the primary path, with export flow and Not Assessed wording still visible."],
  ["Trust copy", "Pre-audit only, no certified audit claim, no 100% secure claim, and no exploit automation language is preserved."],
  ["Provider honesty", "AI, Slither, Aderyn, Mythril, GoPlus, Etherscan, and payments stay pending unless real providers are configured."],
  ["Mobile", "375px+ screens should avoid horizontal overflow, clipped CTAs, and unreadable cards."],
  ["Accessibility", "Keyboard shortcut uses Ctrl/⌘K, Escape closes modal, focus styles stay visible, reduced-motion is supported."],
];

const deployChecks = [
  "Run npm run typecheck before deploy.",
  "Run npm run build before deploy.",
  "Verify Vercel env only contains frontend public env keys.",
  "Verify Render backend env is separate and secrets are not committed.",
  "Click unified scanner, report builder, dashboard, pricing, trust, and limitations after deploy.",
  "Keep payment activation deferred until real order, checkout, webhook, and audit logs are tested.",
];

export default function LaunchQaPage() {
  return (
    <main className="quantum-module-screen mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="module-hero-panel p-6 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.82fr] lg:items-center">
          <div>
            <p className="section-label">Launch QA board</p>
            <h1 className="mt-4 text-4xl font-black sm:text-6xl">Final UI readiness pass before public beta traffic.</h1>
            <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
              This page is a lightweight frontend checklist for the public beta UI. It does not change scanner logic, activate providers, or create fake security results.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="btn-primary">Test unified scanner →</Link>
              <Link href="/feature-status" className="btn-secondary">Review feature status</Link>
              <Link href="/production-deployment-qa" className="btn-secondary">Production deployment QA</Link>
            </div>
          </div>
          <div className="glass-tile p-5">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">Global QA tools</p>
            <div className="mt-4 grid gap-3">
              {[
                "Global Ctrl/⌘K command palette",
                "Scroll progress indicator",
                "Pre-audit disclaimer ribbon",
                "Mobile-safe command navigation",
              ].map((item, index) => (
                <div key={item} className="command-line">
                  <span className="kbd-chip">0{index + 1}</span>
                  <span className="text-sm text-slate-300">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {checks.map(([title, text]) => (
          <article key={title} className="glass-tile p-5">
            <p className="text-lg font-black text-white">{title}</p>
            <p className="mt-3 text-sm leading-6 text-slate-400">{text}</p>
          </article>
        ))}
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="glass-tile p-6">
          <p className="section-label">Shortcut</p>
          <h2 className="mt-3 text-2xl font-black">Use the command palette for fast QA.</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            Press <span className="kbd-chip">Ctrl</span> + <span className="kbd-chip">K</span> on Windows/Linux or <span className="kbd-chip">⌘</span> + <span className="kbd-chip">K</span> on macOS to jump across scanner, trust, report, and dashboard pages.
          </p>
        </div>
        <div className="glass-tile p-6">
          <p className="section-label">Deploy checks</p>
          <ul className="mt-4 grid gap-3 text-sm leading-6 text-slate-300">
            {deployChecks.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-cyan shadow-[0_0_14px_rgba(6,182,212,.55)]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
