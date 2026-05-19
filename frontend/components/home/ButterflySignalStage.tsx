const wingSignals = ["Website", "dApp", "API", "Solidity", "Wallet", "GitHub", "OpSec", "Report"] as const;

type ButterflySignalStageProps = {
  tone?: "intro" | "service" | "compact";
};

export function ButterflySignalStage({ tone = "intro" }: ButterflySignalStageProps) {
  return (
    <div className={`butterfly-signal-stage butterfly-signal-stage-${tone}`} aria-label="Animated Web3Guard butterfly signal visual">
      <div className="butterfly-nebula" aria-hidden="true" />
      <div className="butterfly-grid" aria-hidden="true" />
      <div className="butterfly-scan-line" aria-hidden="true" />

      <div className="butterfly-wing butterfly-wing-left butterfly-wing-left-top" aria-hidden="true" />
      <div className="butterfly-wing butterfly-wing-left butterfly-wing-left-bottom" aria-hidden="true" />
      <div className="butterfly-wing butterfly-wing-right butterfly-wing-right-top" aria-hidden="true" />
      <div className="butterfly-wing butterfly-wing-right butterfly-wing-right-bottom" aria-hidden="true" />
      <div className="butterfly-body" aria-hidden="true" />
      <div className="butterfly-core-mark" aria-hidden="true">W3G</div>

      <div className="butterfly-particles" aria-hidden="true">
        {wingSignals.map((signal, index) => (
          <span key={signal} className={`butterfly-particle butterfly-particle-${index + 1}`}>
            {signal}
          </span>
        ))}
      </div>
    </div>
  );
}
