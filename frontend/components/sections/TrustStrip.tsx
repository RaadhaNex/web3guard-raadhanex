const items = [
  { icon: "🛡", text: "Pre-audit only" },
  { icon: "🔍", text: "Passive checks" },
  { icon: "✋", text: "No exploits" },
  { icon: "📋", text: "Manual review available" },
  { icon: "🌐", text: "Hindi support" },
];

export function TrustStrip() {
  return (
    <section className="border-y border-cyan/[0.08] bg-cyan/[0.02]">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-2 px-4 py-4 sm:px-6 lg:px-8">
        {items.map(({ icon, text }) => (
          <div key={text} className="inline-flex items-center gap-2 rounded-full border border-white/[0.07] bg-white/[0.02] px-3.5 py-1.5 text-xs font-semibold text-slate-300">
            <span>{icon}</span>
            <span>{text}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
