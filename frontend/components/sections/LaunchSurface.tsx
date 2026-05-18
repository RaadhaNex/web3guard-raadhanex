import { modules } from "@/lib/constants";
import Link from "next/link";

const icons: Record<string, string> = {
  "unified-url":      "🔗", "contract":         "📄", "website":          "🌐",
  "website-advanced": "🔎", "dapp":             "⚡", "api":              "🔌",
  "api-deep":         "🧪", "wallet":           "👛", "wallet-risk":      "🛡",
  "admin-opsec":      "🔐", "static-analysis":  "🔬", "deep-analysis":    "🧠",
  "github":           "🐙", "contract-address": "📍", "permission-map":   "🗺",
  "launch-transparency":"🔍","contract-diff":   "↔",  "upgrade-safety":   "⬆",
  "monitoring-lite":  "📡", "cross-chain":      "⛓",
};

export function LaunchSurface() {
  const display = modules.slice(0, 9);
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="text-center mb-10">
        <p className="section-label">Full launch surface</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">
          Web3 launch risk goes beyond smart contracts.
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">
          Web3Guard AI reviews the areas small founders typically miss — from contract code to wallet UX, admin keys, and website headers.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {display.map(({ key, title, href, description }) => (
          <Link
            key={key} href={href}
            className="group flex gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 transition hover:border-cyan/25 hover:bg-white/[0.04]"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.04] text-lg">
              {icons[key] ?? "🔍"}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-white truncate">{title}</p>
              <p className="mt-1 text-xs leading-5 text-slate-400 line-clamp-2">{description}</p>
            </div>
            <svg className="mt-1 ml-auto shrink-0 text-slate-600 transition group-hover:text-cyan" width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M1.5 6.5h10M7.5 2.5l4 4-4 4"/></svg>
          </Link>
        ))}
      </div>

      <div className="mt-6 text-center">
        <Link href="/scanner" className="btn-secondary text-sm">View all scanners →</Link>
      </div>
    </section>
  );
}
