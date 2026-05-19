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
    <div className="command-card p-6">
      <div className="flex items-center gap-5">
        <div className="relative h-24 w-24 shrink-0">
          <svg width="96" height="96" viewBox="0 0 96 96" className="drop-shadow-[0_0_18px_rgba(6,182,212,.16)]">
            <circle cx="48" cy="48" r={r} fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth="8" />
            <circle
              cx="48"
              cy="48"
              r={r}
              fill="none"
              stroke={color}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circ}`}
              strokeDashoffset="0"
              transform="rotate(-90 48 48)"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-black leading-none text-white">{score}</span>
            <span className="mt-1 text-[0.65rem] text-slate-500">/100</span>
          </div>
        </div>

        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Launch confidence</p>
          <p className="mt-2 text-lg font-black leading-tight" style={{ color: risk.color }}>{risk.text}</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">{label}</p>
        </div>
      </div>
    </div>
  );
}
