const penalties = [
  ["Critical", "-25", "Fund loss, takeover, mint abuse, or major launch-blocking risk"],
  ["High", "-15", "Serious issue needing fix or manual review"],
  ["Medium", "-8", "Important readiness risk that should be fixed before launch"],
  ["Low", "-3", "Recommended launch hardening improvement"],
  ["Info", "-1", "Best-practice note or transparency improvement"],
];

const weights = [
  ["Smart Contract", "35%"],
  ["Website Surface", "15%"],
  ["dApp Frontend", "15%"],
  ["API Backend", "15%"],
  ["Wallet Flow", "10%"],
  ["Admin OpSec", "10%"],
];

const labels = [
  ["90–100", "Launch Ready with Minor Notes"],
  ["75–89", "Low Risk, Fix Recommended"],
  ["60–74", "Medium Risk, Fix Before Launch"],
  ["40–59", "High Risk, Manual Review Recommended"],
  ["0–39", "Critical Launch Risk"],
];

export default function MethodologyPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Methodology</p>
      <h1 className="mt-3 max-w-4xl text-4xl font-black sm:text-5xl">How Web3Guard AI scores launch readiness.</h1>
      <p className="mt-4 max-w-3xl text-slate-400">
        Each module starts at 100. Findings reduce score by severity and confidence. Overall readiness uses weighted scoring across contract, website, dApp, API, wallet flow, and founder/admin OpSec.
      </p>

      <div className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="card overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/[0.04] text-slate-200"><tr><th className="p-4">Severity</th><th className="p-4">Penalty</th><th className="p-4">Meaning</th></tr></thead>
            <tbody>{penalties.map((row) => <tr key={row[0]} className="border-t border-white/10"><td className="p-4 font-bold">{row[0]}</td><td className="p-4 mono">{row[1]}</td><td className="p-4 text-slate-400">{row[2]}</td></tr>)}</tbody>
          </table>
        </div>
        <div className="card p-6">
          <h2 className="text-2xl font-black">Module weights</h2>
          <div className="mt-5 space-y-3">
            {weights.map(([module, weight]) => (
              <div key={module} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm">
                <span className="font-bold">{module}</span><span className="mono text-cyan">{weight}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-5">
        {labels.map(([range, label]) => <div key={range} className="card p-5"><div className="mono text-cyan">{range}</div><p className="mt-2 text-sm font-bold text-slate-200">{label}</p></div>)}
      </div>

      <div className="mt-8 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100">
        Scoring is preliminary readiness scoring, not a certified audit score. If a module is not provided, the report shows “Not assessed” and calculates available score separately.
      </div>
    </div>
  );
}
