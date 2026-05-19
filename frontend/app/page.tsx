import Link from "next/link";
import { HomeAuthPrompt } from "@/components/home/HomeAuthPrompt";
import { brand } from "@/lib/constants";

const states = [
  ["Assessed", "Evidence exists and a real rule, provider, or tool has evaluated it."],
  ["Not Assessed", "No evidence or provider was available, so Web3Guard does not guess."],
  ["Manual Review Required", "Human triage is still required before launch decisions."],
];

const web3Info = [
  ["Website & dApp", "HTTPS, security headers, policy pages, wallet-connect UX, phishing warnings, and launch copy risks."],
  ["Smart contracts", "Solidity source, verified contract checks, static-analysis availability, ownership, upgrades, and permission mapping."],
  ["API & admin", "Auth, CORS, webhooks, rate limits, dashboard exposure, admin OpSec, MFA, and role separation."],
  ["Dependencies", "OSV/CISA starter intelligence for known package and ecosystem risks when evidence is available."],
];

const flow = [
  ["01", "Open Home", "Founder sees what Web3Guard checks, what it cannot promise, and why the product is pre-audit only."],
  ["02", "Start scan", "Submit an owned URL, launch surface, contract source, GitHub repo, or supporting evidence."],
  ["03", "Read results", "Separate assessed findings from Not Assessed, Tool Not Installed, Needs API Key, and Manual Review Required."],
  ["04", "Export report", "Use the ₹999 pilot readiness report path after payment validation is configured."],
];

const surfaces = ["Website", "dApp", "API", "Contract", "Dependencies", "Wallet UX", "GitHub", "Admin OpSec"];

export default function HomePage() {
  return (
    <>
      <section className="clean-hero border-b border-white/[0.07]">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-20">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.035] px-3.5 py-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan" />
              <span className="text-[11px] font-black uppercase tracking-[0.20em] text-cyan">Home · Web3 launch security overview</span>
            </div>

            <div className="mt-7 rounded-[28px] border border-cyan/15 bg-cyan/[0.045] p-5 shadow-[0_18px_80px_rgba(6,182,212,.07)] sm:p-6">
              <p className="text-xs font-black uppercase tracking-[0.24em] text-cyan">{brand.company}</p>
              <h1 className="mt-3 text-[clamp(2.35rem,6vw,4.7rem)] font-black leading-[0.96] tracking-[-0.075em] text-white">
                {brand.product}
                <span className="block text-gradient">by {brand.company}</span>
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-8 text-slate-400 sm:text-lg">
                India-first Web3 founder pre-audit launch readiness scanner. Use this home page as the first landing view for founders who need to understand what is checked before they start a scan.
              </p>
            </div>

            <h2 className="mt-8 text-[clamp(2rem,5vw,4rem)] font-black leading-[0.98] tracking-[-0.07em] text-white">
              Web3 launch readiness,
              <span className="block text-gradient">explained before the scan.</span>
            </h2>

            <p className="mt-5 max-w-2xl text-base leading-8 text-slate-400 sm:text-lg">
              Web3Guard helps founders review website, dApp, API, smart-contract, wallet, GitHub, dependency, and admin OpSec readiness. It shows what was assessed, what was not assessed, and what needs manual review.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Link href="/scanner/unified-url" className="btn-primary">Start readiness scan →</Link>
              <HomeAuthPrompt />
              <Link href="/docs" className="btn-secondary">Understand Web3 risks</Link>
            </div>

            <p className="mt-4 text-xs leading-5 text-slate-500">
              Pre-audit readiness only · Not a certified audit · No private key or seed phrase collection · No wallet signing · No exploit automation
            </p>

            <div className="mt-6 grid gap-2 text-xs text-slate-500 sm:grid-cols-3">
              {states.map(([title, text]) => (
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
                <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">Home flow</p>
                <h2 className="mt-2 text-2xl font-black text-white">Home → Scan → Results → Report</h2>
              </div>
              <span className="sev-info">Beta</span>
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
              Missing tools and providers must show Tool Not Installed, Provider Not Configured, Needs API Key, Manual, or Not Assessed. Web3Guard must never show fake pass, fake score, or certified-audit claims.
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-4">
          {web3Info.map(([title, text]) => (
            <div key={title} className="clean-panel p-5">
              <p className="font-black text-white">{title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-14 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="clean-panel p-6 md:col-span-1">
            <p className="section-label">Focus</p>
            <h2 className="mt-3 text-2xl font-black">A clean Home for first-time visitors.</h2>
            <p className="mt-3 text-sm leading-7 text-slate-400">
              When a user opens the site, they land here first. The top header keeps simple navigation, while Web3Guard AI by RAADHANEX branding stays visible and the Home hero explains the product clearly.
            </p>
          </div>
          <div className="clean-panel p-6 md:col-span-2">
            <p className="section-label">Launch surfaces</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {surfaces.map((surface) => (
                <span key={surface} className="rounded-full border border-white/[0.08] bg-white/[0.035] px-3 py-1.5 text-xs font-bold text-slate-300">
                  {surface}
                </span>
              ))}
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                ["Real evidence", "Only assessed inputs appear as assessed findings."],
                ["Clear gaps", "Missing modules remain separated from confidence."],
                ["Safer report", "Limitations and non-audit wording stay visible."],
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
              <p className="section-label">Beta launch</p>
              <h2 className="mt-3 text-3xl font-black">Ready for first founder feedback after validation.</h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
                Before sending to the first 10 users, validate the scanner route, result states, report export, Razorpay test flow, and the public safety wording.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
              <Link href="/launch-pack" className="btn-secondary">First 10 users checklist</Link>
              <Link href="/pricing" className="btn-primary">Check ₹999 pilot flow →</Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
