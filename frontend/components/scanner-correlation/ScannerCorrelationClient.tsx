"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";
import { loadLatestUnifiedScan } from "@/lib/latestUnifiedScan";

type Status = {
  ok: boolean;
  version: string;
  purpose: string;
  safe_status_labels: string[];
  detection_surfaces: Array<{ id: string; label: string; sources: string[]; best_for: string[]; limitations: string[] }>;
  not_supported: string[];
  required_disclaimer: string;
  references: Record<string, string>;
};

type Playbook = {
  ok: boolean;
  playbooks: Array<{ id: string; title: string; when_to_use: string; steps: string[] }>;
  attack_path_templates: Array<{ id: string; title: string; severity: string; impact: string; future_risk: string; fix: string }>;
  safe_wording: string;
};

type FindingInput = {
  title: string;
  description: string;
  severity: string;
  source: string;
  module: string;
  cve_ids: string;
  cwe_ids: string;
  known_exploited: boolean;
  public_poc: boolean;
  requires_auth: boolean;
  status: string;
};

const initialFindings: FindingInput[] = [];


const defaultFinding: FindingInput = {
  title: "BOLA/IDOR risk in project API",
  description: "Endpoint accepts project_id/user_id without clear object ownership verification.",
  severity: "high",
  source: "Semgrep",
  module: "api_backend",
  cve_ids: "",
  cwe_ids: "CWE-862,CWE-863",
  known_exploited: false,
  public_poc: false,
  requires_auth: true,
  status: "Assessed",
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/35 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

function SeverityBadge({ severity }: { severity: string }) {
  const normalized = severity.toLowerCase();
  const tone = normalized === "critical"
    ? "border-red-300/30 bg-red-400/10 text-red-100"
    : normalized === "high"
      ? "border-orange-300/30 bg-orange-400/10 text-orange-100"
      : normalized === "medium"
        ? "border-amber-300/30 bg-amber-400/10 text-amber-100"
        : "border-cyan/30 bg-cyan/10 text-cyan";
  return <span className={`rounded-full border px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.16em] ${tone}`}>{severity}</span>;
}

function PriorityBadge({ priority }: { priority: string }) {
  const tone = priority === "P0"
    ? "border-red-300/30 bg-red-500/10 text-red-100"
    : priority === "P1"
      ? "border-orange-300/30 bg-orange-400/10 text-orange-100"
      : priority === "P2"
        ? "border-amber-300/30 bg-amber-400/10 text-amber-100"
        : "border-white/10 bg-white/[0.04] text-slate-300";
  return <span className={`rounded-full border px-2.5 py-1 text-xs font-black ${tone}`}>{priority}</span>;
}

function splitIds(value: string) {
  return value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function normalizeSeverity(value: unknown) {
  const text = asString(value, "info").toLowerCase();
  return ["critical", "high", "medium", "low", "info"].includes(text) ? text : "info";
}

function toFindingInput(value: unknown, fallbackModule = "scan_evidence"): FindingInput | null {
  if (!isRecord(value)) return null;
  const title = asString(value.title, asString(value.recommended_action, ""));
  if (!title) return null;
  return {
    title,
    description: asString(value.description, asString(value.business_impact, asString(value.developer_explanation, "Evidence from latest scan."))),
    severity: normalizeSeverity(value.severity),
    source: asString(value.source, "Latest scan"),
    module: asString(value.module, fallbackModule),
    cve_ids: asArray(value.cve_ids).join(","),
    cwe_ids: asArray(value.cwe_ids).join(","),
    known_exploited: Boolean(value.known_exploited),
    public_poc: Boolean(value.public_poc),
    requires_auth: Boolean(value.requires_auth),
    status: asString(value.status, "Assessed"),
  };
}

function importLatestScanFindings(): FindingInput[] {
  const latest = loadLatestUnifiedScan();
  if (!latest) return [];
  const imported: FindingInput[] = [];

  for (const item of asArray(latest.combined_report?.top_findings)) {
    const finding = toFindingInput(item, "combined_report");
    if (finding) imported.push(finding);
  }

  for (const item of asArray(latest.priority_actions)) {
    const finding = toFindingInput(item, "priority_action");
    if (finding) imported.push(finding);
  }

  const surface = isRecord(latest.surface_hints) ? latest.surface_hints : {};
  const staticAnalysis = isRecord(surface.static_analysis) ? surface.static_analysis : {};
  const github = isRecord(surface.github_dependency_risk) ? surface.github_dependency_risk : {};
  const api = isRecord(surface.api_admin_exposure) ? surface.api_admin_exposure : {};

  for (const [fallbackModule, list] of [
    ["static_analysis", asArray(staticAnalysis.findings)],
    ["github_dependency", asArray(github.findings)],
    ["api_admin_exposure", asArray(api.findings)],
  ] as const) {
    for (const item of list) {
      const finding = toFindingInput(item, fallbackModule);
      if (finding) imported.push(finding);
    }
  }

  const seen = new Set<string>();
  return imported.filter((item) => {
    const key = `${item.title}:${item.module}:${item.source}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function ScannerCorrelationClient() {
  const [status, setStatus] = useState<Status | null>(null);
  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [findings, setFindings] = useState<FindingInput[]>(initialFindings);
  const [result, setResult] = useState<any>(null);
  const [attackPath, setAttackPath] = useState<any>(null);
  const [claim, setClaim] = useState("Web3Guard correlates scanner evidence into prioritized pre-audit risks. It does not guarantee all bugs are found.");
  const [claimResult, setClaimResult] = useState<any>(null);
  const [assetContext, setAssetContext] = useState({ internet_exposed: true, holds_funds: true });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [statusData, playbookData] = await Promise.all([
          apiGet<Status>("/scanner-correlation/status"),
          apiGet<Playbook>("/scanner-correlation/playbook"),
        ]);
        setStatus(statusData);
        setPlaybook(playbookData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load scanner correlation engine");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    const latestFindings = importLatestScanFindings();
    if (latestFindings.length) setFindings(latestFindings);
  }, []);

  const payload = useMemo(() => ({
    project_name: "Latest scan correlation",
    asset_context: assetContext,
    assessed_modules: {
      slither_or_contract_static: true,
      semgrep_or_code_static: true,
      osv_nvd_cisa: true,
      authorized_web_dast: false,
      manual_business_logic_review: false,
    },
    findings: findings.map((finding) => ({
      title: finding.title,
      description: finding.description,
      severity: finding.severity,
      source: finding.source,
      module: finding.module,
      cve_ids: splitIds(finding.cve_ids),
      cwe_ids: splitIds(finding.cwe_ids),
      known_exploited: finding.known_exploited,
      public_poc: finding.public_poc,
      requires_auth: finding.requires_auth,
      status: finding.status,
    })),
    real_only_acknowledged: true,
  }), [assetContext, findings]);

  async function prioritize() {
    setError(null);
    try {
      setResult(await apiPost("/scanner-correlation/prioritize", payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Correlation failed");
    }
  }

  async function buildAttackPath() {
    setError(null);
    try {
      setAttackPath(await apiPost("/scanner-correlation/attack-path", payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Attack-path build failed");
    }
  }

  async function checkClaim() {
    setError(null);
    try {
      setClaimResult(await apiPost("/scanner-correlation/claim-check", { text: claim, real_only_acknowledged: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    }
  }

  function updateFinding(index: number, patch: Partial<FindingInput>) {
    setFindings((current) => current.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  if (loading) return <CommandLoadingState label="Loading scanner correlation engine..." />;

  return (
    <section className="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-6">
        {error ? <CommandNotice tone="danger" title="Correlation engine error" text={error} /> : null}

        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Phase 43 engine</p>
              <h2 className="mt-2 text-2xl font-black text-white">Correlation setup</h2>
            </div>
            <StatusPill status={status?.ok ? "Correlation live" : "Not assessed"} />
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-400">{status?.required_disclaimer}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm font-semibold text-slate-300">
              <input type="checkbox" checked={assetContext.internet_exposed} onChange={(e) => setAssetContext({ ...assetContext, internet_exposed: e.target.checked })} />
              Internet-exposed asset
            </label>
            <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm font-semibold text-slate-300">
              <input type="checkbox" checked={assetContext.holds_funds} onChange={(e) => setAssetContext({ ...assetContext, holds_funds: e.target.checked })} />
              Holds funds / unlocks value
            </label>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="btn-primary" onClick={prioritize}>Prioritize findings</button>
            <button className="btn-secondary" onClick={buildAttackPath}>Build attack-path map</button>
            <button className="btn-secondary" onClick={() => setFindings([...findings, defaultFinding])}>Add finding</button>
            <button className="btn-secondary" onClick={() => setFindings(importLatestScanFindings())}>Load latest scan evidence</button>
          </div>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Imported scanner findings</p>
          <h2 className="mt-2 text-2xl font-black text-white">Evidence to correlate</h2>
          <div className="mt-5 grid gap-4">
            {!findings.length ? <p className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-slate-400">No latest scan findings were found. Run a unified scan first, then click Load latest scan evidence, or add a real finding manually.</p> : null}
            {findings.map((finding, index) => (
              <div key={`${finding.title}-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-black text-white">Finding {index + 1}</p>
                  <button className="text-xs font-bold text-red-200" onClick={() => setFindings((current) => current.filter((_, i) => i !== index))}>Remove</button>
                </div>
                <div className="mt-3 grid gap-3">
                  <input className="form-input" value={finding.title} onChange={(e) => updateFinding(index, { title: e.target.value })} placeholder="Finding title" />
                  <textarea className="form-input min-h-20" value={finding.description} onChange={(e) => updateFinding(index, { description: e.target.value })} placeholder="Description/evidence" />
                  <div className="grid gap-3 sm:grid-cols-3">
                    <select className="form-input" value={finding.severity} onChange={(e) => updateFinding(index, { severity: e.target.value })}>
                      {['critical', 'high', 'medium', 'low', 'info'].map((item) => <option key={item} value={item}>{item}</option>)}
                    </select>
                    <input className="form-input" value={finding.source} onChange={(e) => updateFinding(index, { source: e.target.value })} placeholder="Slither/Semgrep/OSV" />
                    <input className="form-input" value={finding.module} onChange={(e) => updateFinding(index, { module: e.target.value })} placeholder="module" />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <input className="form-input" value={finding.cve_ids} onChange={(e) => updateFinding(index, { cve_ids: e.target.value })} placeholder="CVE IDs" />
                    <input className="form-input" value={finding.cwe_ids} onChange={(e) => updateFinding(index, { cwe_ids: e.target.value })} placeholder="CWE IDs" />
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs font-bold text-slate-300">
                    <label className="flex items-center gap-2"><input type="checkbox" checked={finding.known_exploited} onChange={(e) => updateFinding(index, { known_exploited: e.target.checked })} /> Known exploited</label>
                    <label className="flex items-center gap-2"><input type="checkbox" checked={finding.public_poc} onChange={(e) => updateFinding(index, { public_poc: e.target.checked })} /> Public PoC</label>
                    <label className="flex items-center gap-2"><input type="checkbox" checked={finding.requires_auth} onChange={(e) => updateFinding(index, { requires_auth: e.target.checked })} /> Requires auth</label>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Claim safety</p>
          <h2 className="mt-2 text-2xl font-black text-white">Block fake scanner claims</h2>
          <textarea className="form-input mt-4 min-h-24" value={claim} onChange={(e) => setClaim(e.target.value)} />
          <button className="btn-secondary mt-3" onClick={checkClaim}>Check wording</button>
          {claimResult ? <div className="mt-4"><JsonBlock value={claimResult} /></div> : null}
        </article>
      </div>

      <div className="space-y-6">
        <article className="clean-panel p-6">
          <p className="section-label">Detection surfaces</p>
          <h2 className="mt-2 text-2xl font-black text-white">Multi-engine coverage map</h2>
          <div className="mt-5 grid gap-3">
            {status?.detection_surfaces.map((surface) => (
              <div key={surface.id} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                <h3 className="font-black text-white">{surface.label}</h3>
                <p className="mt-2 text-xs font-bold uppercase tracking-[0.16em] text-cyan">Sources</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">{surface.sources.join(' · ')}</p>
                <p className="mt-2 text-xs font-bold uppercase tracking-[0.16em] text-red-200">Limitations</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">{surface.limitations.join(' · ')}</p>
              </div>
            ))}
          </div>
        </article>

        {result ? (
          <article className="clean-panel p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="section-label">Prioritized result</p>
                <h2 className="mt-2 text-2xl font-black text-white">Top priority: {result.top_priority}</h2>
              </div>
              <StatusPill status="Correlated" />
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-4">
              {Object.entries(result.priority_summary || {}).map(([key, value]) => (
                <div key={key} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">{key}</p>
                  <p className="mt-1 text-2xl font-black text-white">{String(value)}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 grid gap-4">
              {(result.correlated_findings || []).map((finding: any) => (
                <div key={finding.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <PriorityBadge priority={finding.priority} />
                    <SeverityBadge severity={finding.severity} />
                    <span className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] font-bold text-slate-400">score {finding.priority_score}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-black text-white">{finding.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{finding.impact}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-400"><span className="font-bold text-white">Future risk:</span> {finding.future_risk}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(finding.correlation_reasons || []).slice(0, 5).map((reason: string) => <span key={reason} className="rounded-full border border-cyan/20 bg-cyan/10 px-3 py-1 text-xs font-bold text-cyan">{reason}</span>)}
                  </div>
                </div>
              ))}
            </div>
            {result.coverage_gaps?.length ? <div className="mt-5"><CommandNotice tone="warning" title="Coverage gaps remain" text={result.recommended_next_action} /></div> : null}
          </article>
        ) : null}

        {attackPath ? (
          <article className="clean-panel p-6">
            <p className="section-label">Attack-path prioritization</p>
            <h2 className="mt-2 text-2xl font-black text-white">Hypothetical chain map</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{attackPath.safe_limitation}</p>
            <div className="mt-5"><JsonBlock value={attackPath} /></div>
          </article>
        ) : null}

        <article className="clean-panel p-6">
          <p className="section-label">Playbooks</p>
          <h2 className="mt-2 text-2xl font-black text-white">What to do after correlation</h2>
          <div className="mt-5 grid gap-3">
            {playbook?.playbooks.map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                <h3 className="font-black text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{item.when_to_use}</p>
                <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm leading-6 text-slate-400">
                  {item.steps.map((step) => <li key={step}>{step}</li>)}
                </ol>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
