export function TrustStrip() {
  const items = ["Pre-audit only", "No exploit automation", "Passive website checks", "Manual review available", "UPI payment supported", "Hinglish explanation ready"];
  return (
    <section className="border-y border-white/10 bg-white/[0.03]">
      <div className="mx-auto grid max-w-7xl gap-3 px-4 py-6 sm:grid-cols-2 sm:px-6 lg:grid-cols-6 lg:px-8">
        {items.map((item) => <div key={item} className="rounded-2xl border border-white/10 bg-black/20 p-3 text-center text-sm font-bold text-slate-200">{item}</div>)}
      </div>
    </section>
  );
}
