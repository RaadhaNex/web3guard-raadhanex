"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";

type Status = {
  ok?: boolean;
  phase_range?: string;
  engine_version?: string;
  purpose?: string;
  real_only_rule?: string;
  safe_scope?: string[];
  phases?: Record<string, string>;
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="max-h-[420px] overflow-auto rounded-3xl border border-white/10 bg-black/35 p-4 text-xs leading-6 text-slate-200">{JSON.stringify(value, null, 2)}</pre>;
}

export function DetectionExpansionClient() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Status>("/detection-expansion/status")
      .then(setStatus)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const phases = Object.entries(status?.phases || {});

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/75 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-200/80">Phases 60–67</p>
        <h1 className="mt-4 max-w-5xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Deep bug discovery without fake exploit claims.
        </h1>
        <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-300 sm:text-base">
          This layer expands real evidence coverage: same-origin crawler, JS/API endpoint discovery, GitHub deep risk, OpenAPI/auth evidence, wallet transaction/signature decoding, business logic review, DeFi simulation artifacts, and false-positive learning.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Run unified scan →</Link>
          <Link href="/results" className="btn-secondary">Open results</Link>
        </div>
      </section>

      {error ? <div className="mt-6 rounded-3xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">{error}</div> : null}

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        <article className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-xl font-black text-white">Engine</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">{status?.engine_version || "Loading..."}</p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-xl font-black text-white">Real-only rule</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">{status?.real_only_rule || "Missing evidence stays Not Assessed."}</p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-xl font-black text-white">Boundary</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">No brute force, DoS, credential stuffing, exploit payloads, wallet signing, or private-key collection.</p>
        </article>
      </section>

      <section className="mt-6 rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-5">
        <h2 className="text-2xl font-black text-white">Included engines</h2>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {phases.map(([phase, title]) => (
            <article key={phase} className="rounded-2xl border border-white/10 bg-black/25 p-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-cyan-200">Phase {phase}</p>
              <h3 className="mt-2 font-black text-white">{title}</h3>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-6 rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-5">
        <h2 className="text-2xl font-black text-white">Status payload</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">Use this page to confirm the backend deployed Phase 60–67. The detailed findings appear inside fresh unified scan results.</p>
        <div className="mt-4"><JsonBlock value={status || { loading: true }} /></div>
      </section>
    </main>
  );
}
