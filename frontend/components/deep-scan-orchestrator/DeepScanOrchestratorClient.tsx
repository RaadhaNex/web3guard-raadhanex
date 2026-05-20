"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";

type StatusPayload = {
  ok?: boolean;
  phase?: string;
  name?: string;
  quick_scan_default?: boolean;
  modes?: string[];
  truth_rule?: string;
  safe_boundaries?: string[];
};

export function DeepScanOrchestratorClient() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<StatusPayload>("/deep-scan-orchestrator/status")
      .then(setStatus)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-white/[0.035] p-6 shadow-2xl shadow-black/30">
        <p className="section-label">Phase 78</p>
        <h1 className="mt-3 text-4xl font-black text-white">Unified Deep Scan Orchestrator</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300">
          The scanner now starts with a clean Quick Scan and unlocks Deep Scan / Expert Evidence only when the user wants stronger coverage. Missing inputs are shown as Not Assessed instead of guessed.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Open scanner</Link>
          <Link href="/results" className="btn-secondary">View latest results</Link>
        </div>
      </section>

      {error ? <p className="mt-5 rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        {[
          ["Quick Scan", "URL + permission only. Auto-runs website headers, CSP, cookies, public exposure paths, JS/API hints, score proof, and coverage gate."],
          ["Deep Scan", "Optional GitHub/API/contract evidence. Runs only when evidence/tool/provider is present."],
          ["Expert Evidence", "Optional Slither/Semgrep/HAR/auth/wallet/business/DeFi artifacts for advanced users and reviewers."],
        ].map(([title, body]) => (
          <article key={title} className="rounded-[1.5rem] border border-white/10 bg-black/20 p-5">
            <h2 className="text-xl font-black text-white">{title}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-300">{body}</p>
          </article>
        ))}
      </section>

      {status ? (
        <section className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="section-label">Live backend status</p>
              <h2 className="mt-2 text-2xl font-black text-white">{status.name || "Orchestrator"}</h2>
              <p className="mt-2 text-sm leading-7 text-slate-300">{status.truth_rule}</p>
            </div>
            <span className="badge badge-cyan">Default: {status.quick_scan_default ? "Quick Scan" : "Custom"}</span>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {(status.safe_boundaries || []).map((item) => <p key={item} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-sm leading-6 text-slate-300">• {item}</p>)}
          </div>
        </section>
      ) : null}
    </main>
  );
}
