import { BlockedClaimsBox, TrustCard, TrustHero } from "@/components/ui/TrustPage";

const splits = [
  ["Website Surface Score", "Public URL passive evidence: HTTPS, headers, robots/sitemap/policy signals, HTML/Web3 hints. No login or exploit testing."],
  ["Contract Rule Score", "Pasted Solidity or verified explorer source analyzed by the local rule engine. Slither/Aderyn/Mythril stay separate unless real tools run."],
  ["Launch Evidence Score", "Evidence completeness: website, contract, dApp, API, wallet, admin OpSec, GitHub inputs. Missing evidence reduces confidence rather than being guessed."],
  ["Overall Launch Confidence", "A readiness confidence label from assessed modules only. It is not a full audit score and not a guarantee of security."],
];

const severities = [
  ["Critical", "Fund loss, takeover, mint abuse, signer compromise, or launch-blocking risk."],
  ["High", "Serious issue that should be fixed or manually reviewed before public launch."],
  ["Medium", "Important readiness risk, missing control, or evidence gap."],
  ["Low", "Hardening recommendation or production hygiene improvement."],
  ["Info", "Transparency, documentation, or contextual note."],
];

export default function MethodologyPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Methodology" title="Evidence-first launch readiness scoring." text="The scoring model separates assessed evidence from missing modules so Web3Guard AI does not show a misleading full audit score." />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-5 lg:grid-cols-4">
          {splits.map(([title, text]) => <TrustCard key={title} title={title}><p>{text}</p></TrustCard>)}
        </div>
        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <TrustCard title="Severity meaning" tone="yellow">
            <div className="space-y-3">
              {severities.map(([sev, text]) => <div key={sev} className="rounded-2xl border border-white/10 bg-black/20 p-4"><strong className="text-white">{sev}</strong><p className="mt-1 text-slate-300">{text}</p></div>)}
            </div>
          </TrustCard>
          <TrustCard title="Not Assessed rule" tone="green">
            <p>Modules with no real input receive <strong>Not Assessed</strong>, not an invented score. Exported reports list these modules separately under evidence required. The available partial score can help prioritize fixes, but public wording must remain “pre-audit readiness reviewed”.</p>
          </TrustCard>
        </div>
        <div className="mt-6"><BlockedClaimsBox /></div>
      </div>
    </main>
  );
}
