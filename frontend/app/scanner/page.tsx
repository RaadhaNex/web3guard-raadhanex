import { modules } from "@/lib/constants";
import { ModuleCard } from "@/components/ui/ModuleCard";

export default function ScannerPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="max-w-3xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Scanner shell</p>
        <h1 className="mt-3 text-4xl font-black sm:text-5xl">Choose a real Web3 launch scanner.</h1>
        <p className="mt-4 text-slate-400">Phase 5.5.1 adds real-only behavior: modules are scored only when real evidence/input is available. Start with Unified URL Scan for website-first launch mapping, then add contract/API/wallet/admin inputs for deeper MVP coverage. No fake AI, fake payment success, fake audit badge, or certified-audit wording.</p>
      </div>
      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map(({ key, ...module }) => <ModuleCard key={key} {...module} />)}
      </div>
    </div>
  );
}
