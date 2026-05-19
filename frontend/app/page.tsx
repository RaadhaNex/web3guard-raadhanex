import Link from "next/link";
import { HomeAuthPrompt } from "@/components/home/HomeAuthPrompt";
import { RiskSignalOrb } from "@/components/home/RiskSignalOrb";
import { brand } from "@/lib/constants";

const signalCards = [
  ["Website & dApp", "HTTPS, policy pages, wallet-connect UX, phishing copy, and launch surface readiness."],
  ["Smart contract", "Verified source, Slither/Semgrep state, ownership, upgrade, permission, and launch-risk signals."],
  ["API & admin", "Auth, CORS, webhook, rate-limit, dashboard exposure, admin OpSec, MFA, and role separation."],
  ["Report path", "Clear assessed/not-assessed states plus a ₹999 pilot readiness report path for first users."],
] as const;

const safetyStates = [
  ["Assessed", "Real evidence or a configured tool/provider reviewed this area."],
  ["Not Assessed", "Web3Guard has no evidence here, so it does not guess or fake a result."],
  ["Manual Review", "Founder or reviewer must verify before making launch decisions."],
] as const;

const launchSteps = [
  ["01", "Start readiness scan", "Submit the owned URL, dApp, contract source, GitHub repo, or API evidence."],
  ["02", "Understand risk", "Read impact, future problem, evidence status, and what was not assessed."],
  ["03", "Export report", "Use the report flow after validation; keep limitations and non-audit wording visible."],
] as const;

const scrollStory = [
  ["01", "Website surface", "Landing page, HTTPS, policy pages, phishing copy, ownership evidence, and launch trust gaps."],
  ["02", "dApp + wallet UX", "Connect flow, risky approval copy, signature warnings, unsupported chains, and user-confusion risk."],
  ["03", "Code + dependency signals", "Solidity source, Slither/Semgrep state, OSV/CISA signals, and tool availability shown honestly."],
  ["04", "Report path", "Assessed, Not Assessed, Manual Review, Needs API Key, and Tool Not Installed stay visible."],
] as const;

const coverage = ["Website", "dApp frontend", "API backend", "Smart contract", "Wallet UX", "GitHub", "Dependencies", "Admin OpSec"] as const;

export default function HomePage() {
  return (
    <>
      <section className="cinematic-fullscreen-home relative isolate overflow-hidden border-b border-white/[0.07]">
        <div className="home-cinematic-bg" aria-hidden="true" />
        <div className="home-floating-beam home-floating-beam-one" aria-hidden="true" />
        <div className="home-floating-beam home-floating-beam-two" aria-hidden="true" />
        <div className="home-hero-orb-full" aria-hidden="true" data-parallax="0.035" data-scroll-motion>
          <RiskSignalOrb variant="hero" />
        </div>

        <div className="home-hero-content mx-auto flex min-h-[calc(100svh-56px)] max-w-7xl items-center px-4 py-16 sm:px-6 lg:px-8">
          <div className="home-hero-copy relative z-10 max-w-[34rem]" data-scroll-motion data-parallax="-0.018">
            <div className="home-kicker">
              <span className="home-kicker-dot" />
              <span>India-first Founder Security OS</span>
              <strong>Clean beta</strong>
            </div>

            <p className="mt-7 text-[0.68rem] font-black uppercase tracking-[0.28em] text-cyan/75">{brand.company}</p>
            <h1 className="mt-4 text-[clamp(2.4rem,5.4vw,5.6rem)] font-black leading-[0.88] tracking-[-0.08em] text-white/85">
              {brand.product}
              <span className="block home-hero-gradient">by {brand.company}</span>
            </h1>

            <p className="mt-6 max-w-xl text-sm leading-7 text-slate-300/72 sm:text-base">
              Evidence-first Web3 launch readiness for founders: website, dApp, API, Solidity code, wallet UX, GitHub, and admin OpSec before a professional audit.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Link href="/scanner/unified-url" className="btn-primary home-hero-cta">Start readiness scan →</Link>
              <HomeAuthPrompt />
              <Link href="/pricing" className="btn-secondary">View ₹999 pilot report</Link>
            </div>

            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              {safetyStates.map(([title, text]) => (
                <div key={title} className="home-state-card">
                  <p>{title}</p>
                  <span>{text}</span>
                </div>
              ))}
            </div>

            <p className="mt-5 max-w-2xl text-xs leading-6 text-slate-500">
              Pre-audit readiness only · Not a certified audit · No security guarantee · No private key or seed phrase collection · No wallet signing · No exploit automation
            </p>
          </div>
        </div>
      </section>

      <section className="cinematic-section mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-4">
          {signalCards.map(([title, text], index) => (
            <div key={title} className="home-glass-card group tilt-card" style={{ ["--card-index" as string]: index }}>
              <span className="home-card-line" />
              <p>{title}</p>
              <small>{text}</small>
            </div>
          ))}
        </div>
      </section>

      <section className="scroll-story-section cinematic-section mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="scroll-story-grid">
          <div className="scroll-story-sticky" data-scroll-motion>
            <p className="section-label">Scroll intelligence</p>
            <h2 className="mt-4 text-3xl font-black tracking-[-0.06em] text-white sm:text-5xl">Cards should move like the reference video.</h2>
            <p className="mt-4 max-w-xl text-sm leading-7 text-slate-400">
              As users scroll, Web3Guard now reveals each readiness layer with cinematic lift, glow, depth, and staggered motion instead of static cards.
            </p>
            <div className="scroll-story-pulse" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
          </div>

          <div className="scroll-story-stack">
            {scrollStory.map(([step, title, text], index) => (
              <article key={step} className="scroll-story-card tilt-card" style={{ ["--card-index" as string]: index }}>
                <div className="scroll-story-card-top">
                  <span>{step}</span>
                  <strong>{title}</strong>
                </div>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="cinematic-section mx-auto max-w-7xl px-4 pb-14 sm:px-6 lg:px-8">
        <div className="grid gap-5 lg:grid-cols-[0.86fr_1.14fr]">
          <div className="clean-panel cinematic-panel p-6 sm:p-8">
            <p className="section-label">What users see first</p>
            <h2 className="mt-4 text-3xl font-black tracking-[-0.06em] text-white">A premium full-screen Home before the scanner.</h2>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              New visitors now land on a visual Web3 overview. If they are not logged in, the page shows a login option to save reports. If they are already logged in, that login CTA stays hidden.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {coverage.map((item) => (
                <span key={item} className="rounded-full border border-white/[0.08] bg-white/[0.035] px-3 py-1.5 text-xs font-bold text-slate-300">
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="clean-panel cinematic-panel p-6 sm:p-8">
            <p className="section-label">Core product journey</p>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {launchSteps.map(([step, title, text]) => (
                <div key={step} className="home-step-card">
                  <span>{step}</span>
                  <p>{title}</p>
                  <small>{text}</small>
                </div>
              ))}
            </div>
            <div className="mt-6 rounded-2xl border border-amber-300/15 bg-amber-300/[0.055] p-4 text-sm leading-6 text-amber-100/85">
              Missing tools and providers must show Tool Not Installed, Provider Not Configured, Needs API Key, Manual, or Not Assessed. Web3Guard must never show fake pass, fake score, or certified-audit claims.
            </div>
          </div>
        </div>
      </section>

      <section className="cinematic-section mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="home-final-cta cinematic-panel">
          <div>
            <p className="section-label">First 10 users</p>
            <h2 className="mt-4 text-3xl font-black tracking-[-0.06em] text-white">Looks premium, stays honest.</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
              The interface can feel high-end like the reference video, while the product still stays safe: pre-audit readiness, clear limitations, no fake monitoring, and no exploit automation.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
            <Link href="/scanner/unified-url" className="btn-primary">Start scan →</Link>
            <Link href="/docs" className="btn-secondary">Read docs</Link>
          </div>
        </div>
      </section>
    </>
  );
}
