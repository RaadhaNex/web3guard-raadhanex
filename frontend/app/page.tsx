import Link from "next/link";
import { HomeAuthPrompt } from "@/components/home/HomeAuthPrompt";
import { ButterflySignalStage } from "@/components/home/ButterflySignalStage";
import { brand } from "@/lib/constants";

const bottomTicker = [
  "Website, dApp, API, Solidity code, wallet UX, GitHub, and admin OpSec before a professional audit.",
  "Assessed: real evidence or a configured tool/provider reviewed this area.",
  "Not Assessed: Web3Guard does not guess or fake a result.",
  "Manual Review: founder or reviewer must verify before launch decisions.",
  "Pre-audit readiness only · Not a certified audit · No security guarantee · No private key or seed phrase collection · No wallet signing · No exploit automation.",
] as const;

const serviceCards = [
  ["Website & dApp", "HTTPS, policy pages, wallet-connect UX, phishing copy, and launch surface readiness."],
  ["Smart contract", "Verified source, Slither/Semgrep state, ownership, upgrade, permission, and launch-risk signals."],
  ["API & admin", "Auth, CORS, webhook, rate-limit, dashboard exposure, admin OpSec, MFA, and role separation."],
  ["Report path", "Clear assessed/not-assessed states plus a ₹999 pilot readiness report path for first users."],
] as const;

const platformModules = [
  ["Website", "Landing trust, HTTPS, policy pages, phishing language, and launch surface gaps."],
  ["dApp frontend", "Wallet-connect copy, risky actions, chain mismatch, and user-confusion signals."],
  ["API backend", "Auth, CORS, webhooks, rate limit, exposed routes, and safe status reporting."],
  ["Smart contract", "Verified source, ownership, upgrade signals, Slither/Semgrep state, and manual gaps."],
  ["Wallet UX", "No signing collection, no seed phrase flow, safer copy, and user warning clarity."],
  ["GitHub", "Dependency signals, public repo hygiene, secret-exposure hints, and release readiness."],
  ["Admin OpSec", "MFA, role separation, dashboard exposure, operational safety, and founder checklist."],
  ["Pilot report", "₹999 readiness report path with assessed, manual, and unavailable-tool states clearly shown."],
] as const;

const workflowCards = [
  ["01", "Open Home", "User sees a cinematic Founder Security OS entry with Web3 risk areas explained visually."],
  ["02", "Start scan", "Founder submits owned website, dApp, GitHub, contract, or API evidence for readiness review."],
  ["03", "Read states", "Each module shows Assessed, Not Assessed, Manual Review, Needs API Key, or Tool Not Installed."],
  ["04", "Pilot report", "The ₹999 path converts serious founders into a cleaner readiness report request."],
] as const;

export default function HomePage() {
  return (
    <>
      <section className="video-hero-home" aria-label="Web3Guard AI home">
        <div className="video-hero-bg" aria-hidden="true" />
        <div className="video-hero-aurora video-hero-aurora-one" aria-hidden="true" />
        <div className="video-hero-aurora video-hero-aurora-two" aria-hidden="true" />
        <div className="video-hero-noise" aria-hidden="true" />

        <div className="video-hero-stage" data-scroll-motion data-parallax="0.028">
          <ButterflySignalStage tone="intro" />
        </div>

        <div className="video-hero-title" data-scroll-motion data-parallax="-0.012">
          <p>{brand.product}</p>
          <span>{brand.company}</span>
        </div>

        <div className="video-hero-actions" data-scroll-motion>
          <Link href="/scanner/unified-url" className="video-hero-primary">Start readiness scan</Link>
          <HomeAuthPrompt />
          <Link href="/pricing" className="video-hero-secondary">₹999 pilot report</Link>
        </div>

        <div className="video-hero-bottom-ticker" aria-label="Web3Guard readiness states">
          <div className="video-ticker-track">
            {[...bottomTicker, ...bottomTicker].map((item, index) => (
              <span key={`${item}-${index}`}>{item}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="video-services-section" aria-label="Our services">
        <div className="video-services-left" data-scroll-motion data-parallax="0.02">
          <p className="video-section-kicker">Our services</p>
          <h2>Founder Security OS for Web3 launch readiness.</h2>
          <p>
            Web3Guard keeps the experience premium like the reference video, but the product stays honest: real evidence only, clear limitations, and no fake audit claim.
          </p>
          <div className="video-left-butterfly">
            <ButterflySignalStage tone="service" />
          </div>
        </div>

        <div className="video-service-card-track">
          {serviceCards.map(([title, text], index) => (
            <article key={title} className="video-service-card" data-scroll-motion style={{ ["--card-index" as string]: index }}>
              <span className="video-card-index">0{index + 1}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="video-feature-section" aria-label="Web3Guard platform modules">
        <div className="video-section-heading" data-scroll-motion>
          <p className="video-section-kicker">What Web3Guard covers</p>
          <h2>Everything a founder should check before serious audit spend.</h2>
          <span>
            The UI shows useful product areas directly instead of long warning text. Safety states still appear inside scan/report flows where they matter.
          </span>
        </div>

        <div className="video-feature-grid">
          {platformModules.map(([title, text], index) => (
            <article key={title} className="video-feature-card" data-scroll-motion style={{ ["--card-index" as string]: index }}>
              <div className="video-feature-icon">{index + 1}</div>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="video-workflow-section" aria-label="Web3Guard workflow">
        <div className="video-workflow-heading" data-scroll-motion>
          <p className="video-section-kicker">Launch flow</p>
          <h2>From first visit to readiness report.</h2>
        </div>

        <div className="video-workflow-grid">
          {workflowCards.map(([step, title, text], index) => (
            <article key={step} className="video-workflow-card" data-scroll-motion style={{ ["--card-index" as string]: index }}>
              <span>{step}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="video-final-cta" data-scroll-motion>
        <div>
          <p className="video-section-kicker">Ready for beta users</p>
          <h2>Start with a clean scan, then convert serious founders into the pilot report.</h2>
        </div>
        <div className="video-final-actions">
          <Link href="/scanner/unified-url" className="video-hero-primary">Start scan</Link>
          <Link href="/docs" className="video-hero-secondary">Read docs</Link>
        </div>
      </section>
    </>
  );
}
