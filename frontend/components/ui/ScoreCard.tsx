export function ScoreCard({ score, label }: { score: number; label: string }) {
  return (
    <div className="card p-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">Launch Readiness Score</p>
          <p className="mt-2 text-5xl font-black tracking-tight text-white">{score}</p>
        </div>
        <div className="h-20 w-20 rounded-full border-8 border-cyan/70 bg-cyan/10" aria-hidden="true" />
      </div>
      <p className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3 text-sm text-slate-300">{label}</p>
    </div>
  );
}
