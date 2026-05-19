"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";

type QaCheck = {
  key: string;
  area: string;
  label: string;
  passed: boolean;
  severity: "critical" | "high" | "medium" | "low" | string;
  status: string;
  evidence: string;
  action: string;
};

type QaStatus = {
  ok: boolean;
  generated_at: string;
  readiness_label: string;
  score: number;
  passed: number;
  total: number;
  production_ready: boolean;
  checks: QaCheck[];
  manual_live_qa_routes: Array<{ path: string; purpose: string }>;
  commands: Record<string, string[]>;
  real_only_note: string;
};

const fallbackCommands = {
  backend: ["cd backend", "python -m pytest -q"],
  frontend: ["cd frontend", "npm run typecheck", "npm run build"],
  git: ["git status", "git add .", 'git commit -m "Run production deployment QA pass"', "git push origin main"],
};

function statusClass(check: QaCheck) {
  if (check.passed) return "border-emerald-400/30 bg-emerald-500/10 text-emerald-100";
  if (check.severity === "critical") return "border-red-400/30 bg-red-500/10 text-red-100";
  if (check.severity === "high") return "border-orange-400/30 bg-orange-500/10 text-orange-100";
  return "border-amber-400/30 bg-amber-500/10 text-amber-100";
}

function areaGroups(checks: QaCheck[]) {
  return checks.reduce<Record<string, QaCheck[]>>((acc, check) => {
    acc[check.area] ||= [];
    acc[check.area].push(check);
    return acc;
  }, {});
}

function CommandBlock({ title, commands }: { title: string; commands: string[] }) {
  return (
    <div className="glass-tile p-5">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">{title}</p>
      <pre className="mono mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs leading-6 text-slate-300">
        {commands.join("\n")}
      </pre>
    </div>
  );
}

export function ProductionDeploymentQaClient() {
  const [status, setStatus] = useState<QaStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<QaStatus>("/production-deployment-qa/status")
      .then((data) => {
        setStatus(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load production deployment QA status."))
      .finally(() => setLoading(false));
  }, []);

  const groups = useMemo(() => areaGroups(status?.checks || []), [status?.checks]);
  const commands = status?.commands || fallbackCommands;

  return (
    <main className="quantum-module-screen mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="module-hero-panel p-6 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.82fr] lg:items-center">
          <div>
            <p className="section-label">Production deployment QA</p>
            <h1 className="mt-4 text-4xl font-black sm:text-6xl">Final live-readiness board before public beta traffic.</h1>
            <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
              This console checks configuration posture, deployment commands, and manual live routes. It does not certify security, activate payments, or invent provider results.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="btn-primary">Test scanner →</Link>
              <Link href="/report/verify" className="btn-secondary">Verify report</Link>
              <Link href="/provider-readiness" className="btn-secondary">Provider readiness</Link>
            </div>
          </div>

          <div className="glass-tile p-5">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">Current status</p>
            {loading ? (
              <p className="mt-5 text-sm text-slate-400">Loading live-readiness posture...</p>
            ) : error ? (
              <p className="mt-5 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>
            ) : (
              <>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <div className="stat-slab p-4">
                    <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Score</p>
                    <p className="mt-2 text-3xl font-black text-white">{status?.score ?? 0}</p>
                  </div>
                  <div className="stat-slab p-4">
                    <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Passed</p>
                    <p className="mt-2 text-3xl font-black text-white">{status?.passed ?? 0}/{status?.total ?? 0}</p>
                  </div>
                </div>
                <p className={`mt-4 rounded-2xl border p-4 text-sm font-bold ${status?.production_ready ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-100" : "border-amber-400/30 bg-amber-500/10 text-amber-100"}`}>
                  {status?.readiness_label}
                </p>
              </>
            )}
          </div>
        </div>
      </section>

      {status?.real_only_note ? (
        <section className="mt-8 rounded-3xl border border-cyan/15 bg-cyan/[0.05] p-5 text-sm leading-7 text-cyan-50">
          <strong>Real-only note:</strong> {status.real_only_note}
        </section>
      ) : null}

      <section className="mt-8 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-5">
          {Object.entries(groups).map(([area, checks]) => (
            <section key={area} className="glass-tile p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-black text-white">{area}</h2>
                <span className="badge badge-cyan">{checks.filter((item) => item.passed).length}/{checks.length} passed</span>
              </div>
              <div className="mt-4 grid gap-3">
                {checks.map((check) => (
                  <article key={check.key} className={`rounded-2xl border p-4 ${statusClass(check)}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-black text-white">{check.label}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] opacity-80">{check.severity} · {check.status}</p>
                      </div>
                      <span className="kbd-chip">{check.passed ? "PASS" : "FIX"}</span>
                    </div>
                    <p className="mt-3 text-sm leading-6 opacity-90"><strong>Evidence:</strong> {check.evidence}</p>
                    {!check.passed ? <p className="mt-2 text-sm leading-6 opacity-90"><strong>Action:</strong> {check.action}</p> : null}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>

        <aside className="space-y-5">
          <section className="glass-tile p-5">
            <p className="section-label">Manual live routes</p>
            <div className="mt-5 grid gap-3">
              {(status?.manual_live_qa_routes || []).map((route) => (
                <Link key={route.path} href={route.path} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/30 hover:bg-cyan/[0.05]">
                  <p className="mono text-sm font-black text-cyan">{route.path}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{route.purpose}</p>
                </Link>
              ))}
            </div>
          </section>

          <CommandBlock title="Backend test" commands={commands.backend || fallbackCommands.backend} />
          <CommandBlock title="Frontend test" commands={commands.frontend || fallbackCommands.frontend} />
          <CommandBlock title="GitHub push" commands={commands.git || fallbackCommands.git} />
        </aside>
      </section>
    </main>
  );
}
