import Link from "next/link";
import { brand } from "@/lib/constants";

export function Hero() {
  return (
    <section className="grid-bg relative overflow-hidden border-b border-white/10">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:py-28">
        <div>
          <span className="badge">Pre-audit launch readiness • Built by {brand.company}</span>
          <h1 className="mt-6 max-w-4xl text-4xl font-black leading-tight tracking-tight sm:text-6xl">
            AI-assisted Web3 launch security review before expensive audits.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            Check smart contracts, websites, dApp frontend, APIs, wallet flows, and founder/admin risks before launch. Beginner-friendly reports with clear paid review options.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/scanner/unified-url" className="btn-primary">Start URL Scan</Link>
            <Link href="/feature-status" className="btn-secondary">See Real Status</Link>
          </div>
          <p className="mt-5 text-sm text-amber-100">{brand.disclaimer}</p>
        </div>
        <div className="card p-6">
          <div className="mb-4 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-3 text-xs text-amber-50">This card is a sample preview, not a fake live result. Real scans show evidence and Not assessed modules.</div>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm text-slate-400">Sample output preview</p>
              <p className="mt-2 text-6xl font-black text-white">82</p>
            </div>
            <div className="rounded-2xl border border-cyan/30 bg-cyan/10 px-4 py-3 text-center">
              <p className="text-xs text-slate-400">Risk</p>
              <p className="font-black text-cyan">Example</p>
            </div>
          </div>
          <div className="mt-6 space-y-3">
            {[
              ["Smart Contract", "Owner centralization needs disclosure"],
              ["Website", "CSP and HSTS missing"],
              ["Wallet Flow", "Unlimited approval warning needed"],
              ["Admin OpSec", "Use multisig before launch"]
            ].map(([title, detail]) => (
              <div key={title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-bold text-white">{title}</p>
                  <span className="badge">Sample</span>
                </div>
                <p className="mt-1 text-sm text-slate-400">{detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
