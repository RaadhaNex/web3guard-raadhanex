import Link from "next/link";

const trustStates = [
  ["Real result", "Only when a tool/provider actually returns evidence."],
  ["Not assessed", "Shown clearly when a module has not been checked yet."],
  ["Needs setup", "API keys, workers, and payment checks stay visible."],
];

const flow = [
  ["01", "Scan", "Paste an owned URL, contract source, package, or launch evidence."],
  ["02", "Review", "See real findings, missing checks, external advisories, and setup gaps."],
  ["03", "Report", "Generate a pre-audit pilot report with limitations and fix priorities."],
  ["04", "Validate", "Use pricing/payment readiness only after Razorpay test mode is configured."],
];

const surfaces = [
  "Website",
  "dApp",
  "API",
  "Contract",
  "Dependencies",
  "Wallet UX",
  "Admin OpSec",
  "Disclosure",
];

export default function HomePage() {
  return (
    <>
      <section className="clean-hero border-b border-white/[0.07]">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-24">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.035] px-3.5 py-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan" />
              <span className="text-[11px] font-black uppercase tracking-[0.20em] text-cyan">Clean beta launch mode</span>
            </div>

            <h1 className="mt-7 text-[clamp(2.65rem,6.5vw,5rem)] font-black leading-[0.94] tracking-[-0.075em] text-white">
              Web3 launch readiness,
              <span className="block text-gradient">without noisy dashboards.</span>
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-400 sm:text-lg">
              A simpler pre-audit scanner for Indian and global Web3 founders. Start with one scan, understand what is assessed, fix the highest-risk gaps, and export an honest pilot report.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/scanner/unified-url" className="btn-primary">Start free scan →</Link>
              <Link href="/report/pilot" className="btn-secondary">View pilot report</Link>
            </div>

            <div className="mt-6 grid gap-2 text-xs text-slate-500 sm:grid-cols-3">
              {trustStates.map(([title, text]) => (
                <div key={title} className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4">
                  <p className="font-black text-slate-200">{title}</p>
                  <p className="mt-1 leading-5">{text}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="clean-panel p-5 sm:p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">Product focus</p>
                <h2 className="mt-2 text-2xl font-black text-white">One path for first users</h2>
              </div>
              <span className="sev-info">Pre-audit</span>
            </div>

            <div className="mt-6 space-y-3">
              {flow.map(([step, title, text]) => (
                <div key={step} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
                  <div className="flex gap-3">
                    <span className="mono grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-cyan/20 bg-cyan/10 text-xs font-black text-cyan">{step}</span>
                    <div>
                      <p className="font-black text-white">{title}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-400">{text}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-2xl border border-amber-300/15 bg-amber-300/[0.055] p-4 text-sm leading-6 text-amber-100/85">
              Web3Guard AI is not a certified audit, does not guarantee 100% security, and never asks for private keys, seed phrases, or wallet signing.
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="clean-panel p-6 md:col-span-1">
            <p className="section-label">Visible navigation</p>
            <h2 className="mt-3 text-2xl font-black">Five main links, not fifty.</h2>
            <p className="mt-3 text-sm leading-7 text-slate-400">
              The main UI now pushes only Scanner, Results, Report, Pricing, and Docs. Dashboard and advanced tools are still available under More.
            </p>
          </div>
          <div className="clean-panel p-6 md:col-span-2">
            <p className="section-label">Coverage surfaces</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {surfaces.map((surface) => (
                <span key={surface} className="rounded-full border border-white/[0.08] bg-white/[0.035] px-3 py-1.5 text-xs font-bold text-slate-300">
                  {surface}
                </span>
              ))}
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                ["Real tools", "Slither/Semgrep/worker checks show real or missing status."],
                ["Real advisories", "OSV/CISA style results stay separate from Web3Guard findings."],
                ["Real revenue", "Razorpay success is shown only after verified payment flow."],
              ].map(([title, text]) => (
                <div key={title} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
                  <p className="font-black text-white">{title}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="clean-panel p-6 sm:p-8">
          <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <p className="section-label">Deployment next</p>
              <h2 className="mt-3 text-3xl font-black">Clean UI first. Then deploy. Then first 10 users.</h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
                The product should now feel less like a phase archive and more like a focused beta scanner. After applying this patch, run tests/build, connect env, deploy Vercel/Render, and validate the ₹999 pilot-report flow with test payments.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
              <Link href="/launch-pack" className="btn-secondary">Open launch pack</Link>
              <Link href="/pricing" className="btn-primary">Check pricing flow →</Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
