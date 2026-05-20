"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Status = {
  ok?: boolean;
  engine_version?: string;
  purpose?: string;
  render_provider_readiness?: Record<string, unknown>;
  vercel_required_public_env?: string[];
  blocked_claims?: string[];
};

const samplePayload = {
  benchmark_samples: [
    {
      sample_id: "known-vulnerable-env-exposure-demo",
      expected_findings: ["public .env exposure"],
      scanner_findings: ["public .env exposure"],
      known_clean: false,
    },
    {
      sample_id: "known-clean-basic-site-demo",
      expected_findings: [],
      scanner_findings: [],
      known_clean: true,
    },
  ],
  triaged_findings: [
    { rule_id: "csp-risky-directive", status: "confirmed" },
    { rule_id: "high-script-count", status: "needs_evidence" },
  ],
  invariant_results: [
    { name: "totalSupply equals balances", passed: true, category: "accounting" },
  ],
  api_test_plan: {
    roles: ["user_a", "user_b"],
    endpoints: ["GET /api/orders/{id}"],
    object_ids: ["order owned by user_a", "order owned by user_b"],
  },
  api_observations: [],
  protocol_context: { uses_oracle: true, has_flash_loan_surface: true },
  invariant_catalog: [{ category: "oracle bounds/TWAP", passed: true }],
  claims: ["Evidence-first pre-audit readiness. Not a certified audit."],
};

function StatePill({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-black uppercase tracking-[0.16em] text-cyan-100">{children}</span>;
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="max-h-[520px] overflow-auto rounded-3xl border border-white/10 bg-black/40 p-4 text-xs leading-6 text-slate-200">{JSON.stringify(value, null, 2)}</pre>;
}

export function AccuracyHardeningClient() {
  const [status, setStatus] = useState<Status | null>(null);
  const [result, setResult] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Status>("/accuracy-hardening/status")
      .then(setStatus)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const readiness = useMemo(() => status?.render_provider_readiness ?? {}, [status]);

  async function runDemoPackage() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiPost("/accuracy-hardening/package", { payload: samplePayload });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/75 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <StatePill>Phase 59</StatePill>
        <h1 className="mt-4 max-w-5xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Accuracy hardening, not fake accuracy claims.
        </h1>
        <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-300 sm:text-base">
          This page reduces the weak points: benchmark proof, false-positive tuning, formal/fuzz artifact parsing, API test-plan maturity, DeFi invariant coverage, and trust-proof rules. It still blocks “100% secure”, “all bugs found”, and certified-audit claims.
        </p>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        <article className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-xl font-black text-white">Engine</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">{status?.engine_version || "Loading status..."}</p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-xl font-black text-white">Output guarantee</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Visible findings need evidence, tool output, supplied artifacts, or reviewer triage. Missing areas stay Not Assessed.</p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-xl font-black text-white">Blocked claims</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">No certified audit, no all-bugs guarantee, no fake customer trust.</p>
        </article>
      </section>

      <section className="mt-6 rounded-[1.7rem] border border-white/10 bg-slate-950/50 p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-black text-white">Provider readiness</h2>
            <p className="mt-1 text-sm text-slate-400">Render/backend environment decides which real engines can run live.</p>
          </div>
          <button onClick={runDemoPackage} disabled={loading} className="rounded-2xl bg-cyan-200 px-5 py-3 text-sm font-black text-slate-950 transition hover:bg-white disabled:opacity-60">
            {loading ? "Running..." : "Run evidence package demo"}
          </button>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(readiness).map(([key, value]) => (
            <div key={key} className="rounded-2xl border border-white/10 bg-black/25 p-4">
              <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">{key}</p>
              <p className="mt-1 break-words text-sm font-bold text-white">{String(value)}</p>
            </div>
          ))}
        </div>
      </section>

      {error && <div className="mt-6 rounded-3xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>}

      {result !== null && result !== undefined && (
        <section className="mt-6 rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-2xl font-black text-white">Hardening package output</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">This is a demo payload format. Use real benchmark samples, triaged findings, API observations, and local invariant artifacts for actual proof.</p>
          <div className="mt-4"><JsonBlock value={result} /></div>
        </section>
      )}

      <section className="mt-6 rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-5">
        <h2 className="text-2xl font-black text-white">What became stronger</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {["Benchmark dataset metrics", "False-positive tuning", "Formal/fuzz artifact bridge", "Two-user API test harness", "DeFi invariant coverage", "Trust proof pack without fake claims"].map((item) => (
            <div key={item} className="rounded-2xl border border-white/10 bg-black/25 p-4 text-sm font-bold text-slate-200">{item}</div>
          ))}
        </div>
      </section>
    </main>
  );
}
