"use client";

import { useEffect, useState } from "react";
import { apiGet, API_BASE } from "@/lib/api";

type QaCheck = {
  key: string;
  status: "pass" | "warning" | "fail";
  label: string;
  detail: unknown;
};

type QaStatus = {
  ok: boolean;
  phase: string;
  environment: string;
  frontend_origin: string;
  backend_url: string;
  manual_upi_verification: boolean;
  certified_audit: boolean;
  summary: { failed: number; warnings: number; passed: number };
  checks: QaCheck[];
};

const frontendRoutes = [
  "/",
  "/scanner",
  "/scanner/unified-url",
  "/scanner/contract",
  "/scanner/website",
  "/scanner/dapp",
  "/scanner/api",
  "/scanner/wallet",
  "/scanner/admin-opsec",
  "/report",
  "/pricing",
  "/methodology",
  "/sample-reports",
  "/trust",
  "/ownership-verification",
  "/feature-status",
  "/scope-refund",
  "/responsible-use",
  "/privacy",
  "/terms",
  "/contact",
  "/admin/leads",
];

function statusClass(status: QaCheck["status"]) {
  if (status === "pass") return "border-emerald-500/40 bg-emerald-500/10 text-emerald-100";
  if (status === "warning") return "border-amber-500/40 bg-amber-500/10 text-amber-100";
  return "border-red-500/40 bg-red-500/10 text-red-100";
}

export function LocalQaClient() {
  const [status, setStatus] = useState<QaStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadStatus() {
    setError(null);
    try {
      const data = await apiGet<QaStatus>("/qa/status");
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach backend QA endpoint.");
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  return (
    <div className="space-y-8">
      <section className="card">
        <div className="badge">Local QA</div>
        <h1 className="mt-4 text-3xl font-semibold text-white">Local QA + Stability Console</h1>
        <p className="mt-3 max-w-3xl text-slate-300">
          Use this page after starting both backend and frontend. It does not fake test results: it reads the live backend QA endpoint and shows env/storage warnings clearly.
        </p>
        <div className="mt-5 flex flex-wrap gap-3 text-sm">
          <span className="rounded-full border border-slate-700 px-4 py-2 text-slate-300">Frontend: http://localhost:3000</span>
          <span className="rounded-full border border-slate-700 px-4 py-2 text-slate-300">Backend: {API_BASE}</span>
          <button className="btn-secondary" onClick={loadStatus}>Recheck backend</button>
        </div>
      </section>

      {error && (
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-5 text-red-100">
          <h2 className="font-semibold">Backend QA endpoint not reachable</h2>
          <p className="mt-2 text-sm">{error}</p>
          <p className="mt-2 text-sm text-red-100/80">Start backend with: <code>uvicorn main:app --reload --host 0.0.0.0 --port 8000</code></p>
        </section>
      )}

      {status && (
        <section className="grid gap-4 md:grid-cols-4">
          <div className="card"><p className="text-slate-400">Passed</p><p className="mt-2 text-3xl font-semibold text-emerald-300">{status.summary.passed}</p></div>
          <div className="card"><p className="text-slate-400">Warnings</p><p className="mt-2 text-3xl font-semibold text-amber-300">{status.summary.warnings}</p></div>
          <div className="card"><p className="text-slate-400">Failed</p><p className="mt-2 text-3xl font-semibold text-red-300">{status.summary.failed}</p></div>
          <div className="card"><p className="text-slate-400">Certified audit?</p><p className="mt-2 text-3xl font-semibold text-white">No</p></div>
        </section>
      )}

      {status && (
        <section className="card">
          <h2 className="text-xl font-semibold text-white">Backend readiness checks</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {status.checks.map((check) => (
              <div key={check.key} className={`rounded-2xl border p-4 ${statusClass(check.status)}`}>
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold">{check.label}</h3>
                  <span className="rounded-full border border-current px-2 py-1 text-xs uppercase">{check.status}</span>
                </div>
                <pre className="mt-3 max-h-32 overflow-auto whitespace-pre-wrap text-xs opacity-90">{JSON.stringify(check.detail, null, 2)}</pre>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card">
        <h2 className="text-xl font-semibold text-white">Manual local test order</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-slate-300">
          <li>Open <a className="link" href={`${API_BASE}/health`} target="_blank">backend /health</a> and <a className="link" href={`${API_BASE}/health/readiness`} target="_blank">/health/readiness</a>.</li>
          <li>Run one contract scan with sample Solidity.</li>
          <li>Run one unified URL scan with a URL you own or are authorized to test.</li>
          <li>Create a UPI payment intent from Pricing and confirm it says manual verification.</li>
          <li>Submit a review request lead.</li>
          <li>Open Admin Leads with ADMIN_TOKEN and export CSV.</li>
          <li>Open Report and test Print / Save as PDF.</li>
        </ol>
      </section>

      <section className="card">
        <h2 className="text-xl font-semibold text-white">Frontend routes to click-test</h2>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {frontendRoutes.map((route) => (
            <a className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-300 hover:border-cyan-400/50 hover:text-white" href={route} key={route}>
              {route}
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
