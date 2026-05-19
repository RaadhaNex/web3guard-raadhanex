import Image from "next/image";

const orbitLabels = ["Website", "dApp", "API", "Wallet", "Contract", "GitHub"] as const;
const signalRows = [
  ["Surface", "URL + dApp + wallet UX", "Assessed only with evidence"],
  ["Code", "Solidity + dependency signals", "Tool state shown clearly"],
  ["Founder OS", "Report, pricing, manual review", "No certified-audit claim"],
] as const;

export function RiskSignalOrb() {
  return (
    <div className="risk-orb-card" aria-label="Animated Web3Guard risk intelligence visual">
      <div className="risk-orb-header">
        <span className="risk-orb-live-dot" />
        <span>Founder Security OS</span>
        <strong>Pre-audit beta</strong>
      </div>

      <div className="risk-orb-stage">
        <div className="risk-orb-glow risk-orb-glow-one" />
        <div className="risk-orb-glow risk-orb-glow-two" />
        <div className="risk-orb-grid" />
        <div className="risk-orb-ring risk-orb-ring-one" />
        <div className="risk-orb-ring risk-orb-ring-two" />
        <div className="risk-orb-ring risk-orb-ring-three" />

        <div className="risk-orbit risk-orbit-one">
          {orbitLabels.slice(0, 3).map((label, index) => (
            <span key={label} className={`risk-orbit-node risk-orbit-node-${index + 1}`}>
              {label}
            </span>
          ))}
        </div>
        <div className="risk-orbit risk-orbit-two">
          {orbitLabels.slice(3).map((label, index) => (
            <span key={label} className={`risk-orbit-node risk-orbit-node-${index + 4}`}>
              {label}
            </span>
          ))}
        </div>

        <div className="risk-orb-core">
          <Image
            src="/brand/kavachwing-emblem-transparent.png"
            alt="Web3Guard AI by RAADHANEX"
            width={150}
            height={150}
            priority
          />
          <span className="risk-orb-core-label">RAADHANEX</span>
        </div>
      </div>

      <div className="risk-orb-signal-list">
        {signalRows.map(([label, title, state]) => (
          <div key={label} className="risk-orb-signal-row">
            <span>{label}</span>
            <strong>{title}</strong>
            <em>{state}</em>
          </div>
        ))}
      </div>
    </div>
  );
}
