import type { ReactNode } from "react";
import Link from "next/link";
import { blockedClaims } from "@/lib/publicBetaContent";

export function TrustHero({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) {
  return (
    <section className="w3g-trust-hero relative overflow-hidden border-b border-white/10">
      <div className="pointer-events-none absolute inset-0 w3g-cyber-grid opacity-70" />
      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <p className="section-label text-risk-yellow">{eyebrow}</p>
        <h1 className="mt-4 max-w-5xl text-4xl font-black leading-tight text-white sm:text-6xl">{title}</h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">{text}</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Run public beta scan</Link>
          <Link href="/feature-status" className="btn-secondary">Check feature status</Link>
        </div>
      </div>
    </section>
  );
}

export function TrustCard({ title, children, tone = "slate" }: { title: string; children: ReactNode; tone?: "slate" | "green" | "yellow" | "red" }) {
  const toneClass = {
    slate: "border-white/10 bg-white/[0.035]",
    green: "border-risk-green/25 bg-risk-green/10",
    yellow: "border-risk-yellow/25 bg-risk-yellow/10",
    red: "border-risk-red/25 bg-risk-red/10",
  }[tone];

  return (
    <section className={`rounded-3xl border p-6 shadow-soft ${toneClass}`}>
      <h2 className="text-xl font-black text-white">{title}</h2>
      <div className="mt-4 text-sm leading-7 text-slate-300">{children}</div>
    </section>
  );
}

export function TrustList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item} className="flex gap-3">
          <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-risk-green" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function BlockedClaimsBox() {
  return (
    <TrustCard title="Blocked wording" tone="red">
      <p>These claims stay blocked unless a real verified process exists. The public beta must not use marketing words that overstate scanner output.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {blockedClaims.map((claim) => (
          <span key={claim} className="rounded-full border border-risk-red/30 bg-risk-red/10 px-3 py-1 text-xs font-black text-red-200">{claim}</span>
        ))}
      </div>
    </TrustCard>
  );
}
