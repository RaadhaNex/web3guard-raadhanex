"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { StatusPill } from "@/components/ui/StatusPill";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type WorkerReadiness = {
  tool: string;
  status: string;
  installed: boolean;
  will_run: boolean;
  enabled_by_env: boolean;
  next_action: string;
};

type ScannerDepthStatus = {
  ok: boolean;
  version: string;
  target: string;
  max_automated_pre_audit_coverage: number;
  security_guarantee_percent: number;
  ready_worker_tools: string[];
  worker_readiness: WorkerReadiness[];
  network_advisory_ready: boolean;
  recommended_env_for_90_depth: string[];
  blocked_claims: string[];
  not_claimed: string[];
};

type CoverageItem = {
  key: string;
  label: string;
  status: string;
  weight: number;
  points: number;
  evidence: string;
  next_action: string;
};

type CoverageResult = {
  ok: boolean;
  version: string;
  project_name: string;
  coverage_depth_percent: number;
  raw_module_points: number;
  max_automated_pre_audit_coverage: number;
  target_gap_to_90: number;
  label: string;
  items: CoverageItem[];
  missing_modules: CoverageItem[];
  blockers: string[];
  next_best_actions: string[];
  safe_wording: { allowed: string; blocked: string[]; required_disclaimer: string };
};

type Roadmap = {
  goal: string;
  phases_inside_phase38: Array<{ order: number; name: string; target_points: number; outcome: string }>;
  minimum_for_90_depth: string[];
  never_claim: string[];
};

const toggles: Array<[keyof FormState, string, string]> = [
  ["slither_assessed", "Slither assessed", "Real Slither JSON parsed from worker output."],
  ["semgrep_assessed", "Semgrep assessed", "App/API/code rules parsed from real Semgrep output."],
  ["osv_checked", "OSV checked", "Dependency advisory lookup ran against real package data."],
  ["cisa_checked", "CISA KEV checked", "CVE aliases matched against KEV catalog."],
  ["github_checked", "GitHub checked", "Read-only repo hygiene evidence exists."],
  ["website_checked", "Website checked", "Passive website/header/config evidence exists."],
  ["api_checked", "API checked", "API/OpenAPI/security config evidence exists."],
  ["wallet_ux_checked", "Wallet UX reviewed", "Manual wallet UX evidence exists; no signing."],
  ["admin_opsec_checked", "Admin OpSec reviewed", "Manual admin/account safety evidence exists."],
  ["foundry_tests_run", "Foundry tests run", "forge test output evidence exists."],
  ["echidna_run", "Echidna run", "Invariant/fuzz evidence exists."],
  ["mythril_run", "Mythril run", "Docker/isolated Mythril evidence exists."],
];

type FormState = {
  project_name: string;
  slither_assessed: boolean;
  aderyn_assessed: boolean;
  semgrep_assessed: boolean;
  osv_checked: boolean;
  cisa_checked: boolean;
  github_checked: boolean;
  website_checked: boolean;
  api_checked: boolean;
  wallet_ux_checked: boolean;
  admin_opsec_checked: boolean;
  foundry_tests_run: boolean;
  echidna_run: boolean;
  mythril_run: boolean;
  evidence_items_count: number;
  report_hash: string;
  critical_findings: number;
  high_findings: number;
  real_only_acknowledged: boolean;
};

const defaultForm: FormState = {
  project_name: "Pilot Web3 Project",
  slither_assessed: true,
  aderyn_assessed: false,
  semgrep_assessed: true,
  osv_checked: true,
  cisa_checked: true,
  github_checked: true,
  website_checked: true,
  api_checked: true,
  wallet_ux_checked: true,
  admin_opsec_checked: true,
  foundry_tests_run: true,
  echidna_run: false,
  mythril_run: false,
  evidence_items_count: 8,
  report_hash: "",
  critical_findings: 0,
  high_findings: 0,
  real_only_acknowledged: true,
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/35 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

function DepthMeter({ value, max }: { value: number; max: number }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="section-label">Scanner coverage depth</p>
          <p className="mt-2 text-5xl font-black tracking-[-0.08em] text-white">{value}%</p>
        </div>
        <p className="text-right text-xs font-bold uppercase tracking-[0.18em] text-slate-500">Max honest cap<br />{max}%</p>
      </div>
      <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-white" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-400">This is pre-audit scanner coverage, not a security guarantee.</p>
    </div>
  );
}

export function ScannerDepthClient() {
  const [status, setStatus] = useState<ScannerDepthStatus | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [form, setForm] = useState<FormState>(defaultForm);
  const [result, setResult] = useState<CoverageResult | null>(null);
  const [claim, setClaim] = useState("Web3Guard gives high-depth pre-audit scanner coverage, not a certified audit.");
  const [claimResult, setClaimResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [statusData, roadmapData] = await Promise.all([
          apiGet<ScannerDepthStatus>("/scanner-depth/status"),
          apiGet<Roadmap>("/scanner-depth/roadmap"),
        ]);
        setStatus(statusData);
        setRoadmap(roadmapData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load scanner depth status");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function evaluate() {
    setError(null);
    try {
      const data = await apiPost<CoverageResult>("/scanner-depth/coverage", form);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Coverage evaluation failed");
    }
  }

  async function checkClaim() {
    setError(null);
    try {
      const data = await apiPost("/scanner-depth/claim-check", { text: claim, real_only_acknowledged: true });
      setClaimResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    }
  }

  const readyCount = useMemo(() => status?.worker_readiness.filter((item) => item.status === "Ready").length ?? 0, [status]);

  if (loading) return <CommandLoadingState label="Loading scanner depth hardening status..." />;

  return (
    <section className="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      {error && <div className="lg:col-span-2"><CommandNotice tone="danger" title="Phase 38 error" text={error} /></div>}

      <div className="space-y-6">
        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Truthful target</p>
              <h2 className="mt-2 text-2xl font-black text-white">90% coverage depth, not 99% security.</h2>
            </div>
            <StatusPill status={`${readyCount}/6 workers ready`} />
          </div>
          <p className="mt-4 text-sm leading-7 text-slate-400">{status?.target}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <Link href="/worker-runs" className="btn-secondary">Worker runs</Link>
            <Link href="/launch-validation" className="btn-secondary">OSV / CISA setup</Link>
          </div>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Evidence toggles</p>
          <h3 className="mt-2 text-xl font-black text-white">Model what is actually assessed.</h3>
          <div className="mt-5 grid gap-3">
            {toggles.map(([key, label, help]) => (
              <label key={key} className="flex cursor-pointer items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.025] p-3">
                <input
                  type="checkbox"
                  checked={Boolean(form[key])}
                  onChange={(event) => setForm((prev) => ({ ...prev, [key]: event.target.checked }))}
                  className="mt-1 h-4 w-4 accent-white"
                />
                <span>
                  <span className="block text-sm font-black text-white">{label}</span>
                  <span className="block text-xs leading-5 text-slate-500">{help}</span>
                </span>
              </label>
            ))}
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <label className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">Evidence count<input className="input mt-2" type="number" min={0} value={form.evidence_items_count} onChange={(e) => setForm((p) => ({ ...p, evidence_items_count: Number(e.target.value) }))} /></label>
            <label className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">Critical findings<input className="input mt-2" type="number" min={0} value={form.critical_findings} onChange={(e) => setForm((p) => ({ ...p, critical_findings: Number(e.target.value) }))} /></label>
            <label className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">High findings<input className="input mt-2" type="number" min={0} value={form.high_findings} onChange={(e) => setForm((p) => ({ ...p, high_findings: Number(e.target.value) }))} /></label>
          </div>
          <button className="btn-primary mt-5 w-full" onClick={evaluate}>Evaluate 90-depth coverage</button>
        </article>
      </div>

      <div className="space-y-6">
        {result ? (
          <>
            <DepthMeter value={result.coverage_depth_percent} max={result.max_automated_pre_audit_coverage} />
            <article className="clean-panel p-6">
              <p className="section-label">Result</p>
              <h3 className="mt-2 text-2xl font-black text-white">{result.label}</h3>
              <p className="mt-3 text-sm text-slate-400">Gap to honest 90-depth target: {result.target_gap_to_90} points.</p>
              <div className="mt-5 grid gap-2">
                {result.next_best_actions.map((action) => <p key={action} className="rounded-2xl border border-white/10 bg-white/[0.025] p-3 text-sm text-slate-300">{action}</p>)}
              </div>
            </article>
            <article className="clean-panel p-6">
              <p className="section-label">Module coverage</p>
              <div className="mt-4 grid gap-3">
                {result.items.map((item) => (
                  <div key={item.key} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="font-black text-white">{item.label}</p>
                      <StatusPill status={`${item.points}/${item.weight} · ${item.status}`} />
                    </div>
                    {item.status !== "Assessed" && <p className="mt-2 text-xs leading-5 text-slate-500">{item.next_action}</p>}
                  </div>
                ))}
              </div>
            </article>
          </>
        ) : (
          <article className="clean-panel p-6">
            <p className="section-label">Start</p>
            <h3 className="mt-2 text-2xl font-black text-white">Click evaluate to see whether this project reaches honest 90-depth coverage.</h3>
            <p className="mt-3 text-sm leading-7 text-slate-400">The model only counts assessed evidence. Missing tools are not converted into fake findings or fake coverage.</p>
          </article>
        )}

        <article className="clean-panel p-6">
          <p className="section-label">Claim guard</p>
          <textarea className="input mt-3 min-h-24" value={claim} onChange={(e) => setClaim(e.target.value)} />
          <button className="btn-secondary mt-3" onClick={checkClaim}>Check wording</button>
          {claimResult && <div className="mt-4"><JsonBlock value={claimResult} /></div>}
        </article>

        {roadmap && (
          <article className="clean-panel p-6">
            <p className="section-label">Roadmap inside Phase 38</p>
            <div className="mt-4 space-y-3">
              {roadmap.phases_inside_phase38.map((item) => (
                <div key={item.order} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                  <p className="font-black text-white">{item.order}. {item.name} <span className="text-slate-500">(+{item.target_points})</span></p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{item.outcome}</p>
                </div>
              ))}
            </div>
          </article>
        )}
      </div>
    </section>
  );
}
