import { modules } from "@/lib/constants";
import { ModuleCard } from "@/components/ui/ModuleCard";

export function LaunchSurface() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="max-w-3xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Full launch surface</p>
        <h2 className="mt-3 text-3xl font-black text-white sm:text-4xl">Not only smart contracts. Web3 launch risk is wider.</h2>
        <p className="mt-4 text-slate-400">Web3Guard AI checks the areas small founders usually miss before launch.</p>
      </div>
      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map(({ key, ...module }) => <ModuleCard key={key} {...module} />)}
      </div>
    </section>
  );
}
