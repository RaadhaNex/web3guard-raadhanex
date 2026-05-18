function ringColor(score: number) {
  if (score >= 85) return "#22c55e";
  if (score >= 65) return "#f59e0b";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

function riskLabel(score: number) {
  if (score >= 90) return { text: "Launch Ready", color: "#22c55e" };
  if (score >= 75) return { text: "Low Risk", color: "#86efac" };
  if (score >= 60) return { text: "Medium Risk", color: "#fde68a" };
  if (score >= 40) return { text: "High Risk", color: "#fdba74" };
  return { text: "Critical Risk", color: "#fca5a5" };
}

export function ScoreCard({ score, label }: { score: number; label: string }) {
  const color = ringColor(score);
  const risk = riskLabel(score);
  const pct = Math.max(0, Math.min(100, score));
  const r = 38;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;

  return (
    <div className="card p-6">
      <div className="flex items-center gap-5">
        {/* Circular progress */}
        <div style={{ position: "relative", width: 96, height: 96, flexShrink: 0 }}>
          <svg width="96" height="96" viewBox="0 0 96 96">
            <circle cx="48" cy="48" r={r} fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth="8" />
            <circle
              cx="48" cy="48" r={r} fill="none"
              stroke={color} strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circ}`}
              strokeDashoffset="0"
              transform="rotate(-90 48 48)"
            />
          </svg>
          <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: "1.5rem", fontWeight: 900, lineHeight: 1, color: "var(--text)" }}>{score}</span>
            <span style={{ fontSize: "0.65rem", color: "var(--muted)", marginTop: 1 }}>/100</span>
          </div>
        </div>

        <div className="min-w-0">
          <p style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: 4 }}>Launch Readiness Score</p>
          <p style={{ fontSize: "1.125rem", fontWeight: 800, color: risk.color, lineHeight: 1.2 }}>{risk.text}</p>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: 4, lineHeight: 1.5 }}>{label}</p>
        </div>
      </div>
    </div>
  );
}
