const items = [
  { icon: "🛡", text: "Pre-audit only" },
  { icon: "🔍", text: "Passive website checks" },
  { icon: "✋", text: "No exploit automation" },
  { icon: "📋", text: "Manual review available" },
  { icon: "💳", text: "UPI accepted" },
  { icon: "🌐", text: "Hindi support" },
];

export function TrustStrip() {
  return (
    <section className="border-y border-white/[0.07]" style={{ background: "rgba(255,255,255,0.015)" }}>
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-2 px-4 py-4 sm:px-6 lg:px-8">
        {items.map(({ icon, text }) => (
          <div key={text} className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3.5 py-1.5 text-xs font-medium text-slate-300">
            <span>{icon}</span>
            <span>{text}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
