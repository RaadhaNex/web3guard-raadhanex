"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiGetText, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { CombinedLaunchReport, Finding, ScanResponse, Severity } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { ReportPreview } from "@/components/report/ReportPreview";

const endpointMap: Record<string, string> = {
  contract: "/scan/contract",
  website: "/scan/website",
  dapp: "/scan/dapp-checklist",
  api: "/scan/api-checklist",
  wallet: "/scan/wallet-checklist",
  "admin-opsec": "/scan/admin-opsec",
};

const moduleTitle: Record<string, string> = {
  contract: "Smart Contract Scanner Engine",
  website: "Website Passive Surface Scanner",
  dapp: "dApp Frontend Checklist",
  api: "API Backend Checklist",
  wallet: "Wallet Flow Checklist",
  "admin-opsec": "Founder/Admin OpSec Checklist",
};

type ChecklistItem = { key: string; label: string; answer: "yes" | "no" | "unknown" };
type RuleInfo = { id: string; name: string; category: string };

const severityOrder: Severity[] = ["critical", "high", "medium", "low", "info"];

export function ScannerClient({ module }: { module: string }) {
  const [projectName, setProjectName] = useState("");
  const [input, setInput] = useState(module === "website" ? "" : sampleContract);
  const [contractType, setContractType] = useState("ERC20");
  const [language, setLanguage] = useState("Hinglish");
  const [frontendCode, setFrontendCode] = useState(sampleDappCode);
  const [packageJson, setPackageJson] = useState(samplePackageJson);
  const [apiBaseUrl, setApiBaseUrl] = useState("");
  const [apiCode, setApiCode] = useState(sampleApiCode);
  const [notes, setNotes] = useState(module === "wallet" ? sampleWalletNotes : module === "admin-opsec" ? sampleAdminNotes : "");
  const [authorized, setAuthorized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [launchReport, setLaunchReport] = useState<CombinedLaunchReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [lastSavedProjectId, setLastSavedProjectId] = useState<string | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [rules, setRules] = useState<RuleInfo[]>([]);

  useEffect(() => {
    if (module !== "contract") return;
    apiGet<{ rules: RuleInfo[] }>("/scan/contract/rules")
      .then((data) => setRules(data.rules))
      .catch(() => setRules([]));
  }, [module]);

  const groupedFindings = useMemo(() => groupFindingsBySeverity(result?.findings || []), [result]);

  async function loadChecklist() {
    if (module === "contract" || module === "website" || checklist.length) return;
    const apiModule = module === "admin-opsec" ? "admin_opsec" : module;
    const data = await apiGet<{ items: ChecklistItem[] }>(`/scan/checklist/${apiModule}`);
    setChecklist(data.items);
  }

  async function loadSample(sampleName: string) {
    setSampleLoading(true);
    setError(null);
    try {
      const code = await apiGetText(`/scan/contract/samples/${sampleName}`);
      setInput(code);
      setResult(null);
      setLaunchReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sample load failed");
    } finally {
      setSampleLoading(false);
    }
  }

  async function runScan() {
    setLoading(true);
    setError(null);
    setResult(null);
    setLaunchReport(null);
    try {
      let payload: unknown;
      if (module === "contract") {
        payload = { project_name: projectName, solidity_code: input, contract_type: contractType, authorization_confirmed: authorized };
      } else if (module === "website") {
        payload = { project_name: projectName, url: input, authorization_confirmed: authorized };
      } else {
        const readyChecklist = checklist.length ? checklist : fallbackChecklist(module);
        if (module === "dapp") {
          payload = {
            project_name: projectName,
            checklist: readyChecklist,
            frontend_code: frontendCode,
            package_json: packageJson,
            notes,
            authorization_confirmed: authorized,
          };
        } else if (module === "api") {
          payload = {
            project_name: projectName,
            checklist: readyChecklist,
            api_base_url: apiBaseUrl,
            api_code: apiCode,
            notes,
            authorization_confirmed: authorized,
          };
        } else {
          payload = { project_name: projectName, checklist: readyChecklist, notes, authorization_confirmed: authorized };
        }
      }
      const data = await apiPost<ScanResponse>(endpointMap[module], payload);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  async function generateLaunchReport() {
    if (!result) return;
    setReportLoading(true);
    setError(null);
    try {
      const data = await apiPost<CombinedLaunchReport>("/report/combined", {
        project_name: projectName,
        reports: [result],
        preferred_language: language,
        include_ai: true,
        report_mode: "pre_audit",
      });
      setLaunchReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report generation failed");
    } finally {
      setReportLoading(false);
    }
  }

  async function dashboardContext() {
    const userId = await getCurrentUserId();
    const token = await getSessionToken();
    return { userId, headers: token ? { Authorization: `Bearer ${token}` } : undefined };
  }

  async function createDashboardProject(headers: HeadersInit | undefined, userId: string) {
    const project = await apiPost<{ project: { id: string } }>("/projects", {
      user_id: userId,
      name: projectName || "Saved Web3Guard Project",
      website_url: module === "website" ? input : null,
      chain: module === "contract" ? contractType : null,
      project_type: moduleTitle[module] || module,
      description: "Created from scanner save action. This is a real saved dashboard record, not a fake audit claim.",
    }, { headers });
    setLastSavedProjectId(project.project.id);
    return project.project.id;
  }

  async function saveResultToDashboard() {
    if (!result) return;
    setSaveLoading(true);
    setSaveMessage(null);
    setError(null);
    try {
      const ctx = await dashboardContext();
      const projectId = lastSavedProjectId || await createDashboardProject(ctx.headers, ctx.userId);
      const criticalHigh = result.findings.filter((finding) => finding.severity === "critical" || finding.severity === "high").length;
      await apiPost("/scan-history", {
        user_id: ctx.userId,
        project_id: projectId,
        module: result.module_score.module,
        project_name: projectName,
        score: result.module_score.score,
        risk_label: result.module_score.risk_label,
        report_id: result.report_id,
        input_hash: result.input_hash,
        findings_count: result.findings.length,
        critical_high_count: criticalHigh,
        status: "saved_from_scanner",
        payload: result,
      }, { headers: ctx.headers });
      setSaveMessage("Scan saved to dashboard as a real record. It is not marked as certified audit.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save scan to dashboard");
    } finally {
      setSaveLoading(false);
    }
  }

  async function saveReportToDashboard() {
    if (!launchReport) return;
    setSaveLoading(true);
    setSaveMessage(null);
    setError(null);
    try {
      const ctx = await dashboardContext();
      const projectId = lastSavedProjectId || await createDashboardProject(ctx.headers, ctx.userId);
      await apiPost("/saved-reports", {
        user_id: ctx.userId,
        project_id: projectId,
        report_id: launchReport.report_id,
        title: `${projectName} Launch Readiness Report`,
        report_hash: launchReport.report_hash,
        overall_score: launchReport.combined.overall_score ?? null,
        available_score: launchReport.combined.available_score ?? null,
        risk_label: launchReport.combined.risk_label,
        visibility: "private",
        status: "saved_from_report_builder",
        payload: launchReport,
      }, { headers: ctx.headers });
      setSaveMessage("Report saved to dashboard as a private real record. Public registry is not live yet.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save report to dashboard");
    } finally {
      setSaveLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8" onMouseEnter={loadChecklist}>
      <div className="mb-8 max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">{module === "website" ? "Passive website surface scanner" : module === "dapp" || module === "api" ? "dApp + API risk scanner" : module === "wallet" || module === "admin-opsec" ? "Wallet + admin OpSec scanner" : "Web3Guard AI scanner module"}</p>
        <h1 className="mt-3 text-3xl font-black sm:text-5xl">{moduleTitle[module]}</h1>
        <p className="mt-4 text-slate-400">
          {module === "website"
            ? "Run safe passive checks for HTTPS, redirects, security headers, robots/sitemap, limited sensitive path hints, external scripts, and launch trust signals. No exploit payloads or aggressive scanning."
            : module === "wallet"
              ? "Review wallet connection, approval, spender, permit/signature, chain mismatch, transaction preview, and anti-phishing UX without connecting to a real wallet or signing anything."
              : module === "admin-opsec"
                ? "Review founder/admin operational security: multisig, timelock, key storage, treasury separation, upgrade admin, MFA, audit logs, signer rotation, and incident response."
                : "RAADHANEX Web3Guard AI creates safe fallback/AI explanations and print-ready launch readiness reports without fake audit claims."}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="card p-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="text-sm font-bold text-slate-200">Project name</label>
              <input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} />
            </div>
            {module === "contract" && (
              <div>
                <label className="text-sm font-bold text-slate-200">Contract type</label>
                <select className="select mt-2" value={contractType} onChange={(e) => setContractType(e.target.value)}>
                  <option>ERC20</option><option>NFT</option><option>Staking</option><option>DAO</option><option>Marketplace</option><option>DeFi</option><option>Other</option>
                </select>
              </div>
            )}
            <div>
              <label className="text-sm font-bold text-slate-200">Report language</label>
              <select className="select mt-2" value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option>English</option><option>Hindi</option><option>Hinglish</option>
              </select>
            </div>
          </div>

          {module === "contract" && (
            <div className="mt-5 rounded-2xl border border-cyan/20 bg-cyan/10 p-4">
              <p className="text-sm font-black text-white">Test with real sample contracts</p>
              <p className="mt-1 text-xs text-slate-300">These are local sample contracts for verifying the scanner engine and report layer.</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                <button type="button" className="btn-secondary text-xs" disabled={sampleLoading} onClick={() => loadSample("vulnerable_token")}>Vulnerable token</button>
                <button type="button" className="btn-secondary text-xs" disabled={sampleLoading} onClick={() => loadSample("safer_token")}>Safer token</button>
                <button type="button" className="btn-secondary text-xs" disabled={sampleLoading} onClick={() => loadSample("upgradeable_init_risk")}>Upgradeable risk</button>
              </div>
            </div>
          )}

          {module === "dapp" && (
            <div className="mt-5 space-y-4 rounded-2xl border border-cyan/20 bg-cyan/10 p-4">
              <div>
                <p className="text-sm font-black text-white">Optional dApp code/package hints</p>
                <p className="mt-1 text-xs text-slate-300">Paste frontend snippets or package.json to detect exposed public secrets, hardcoded RPC/contract addresses, dangerous rendering, auto-connect, approval risk, and wallet UX gaps.</p>
              </div>
              <div>
                <label className="text-sm font-bold text-slate-200">Frontend code snippet</label>
                <textarea className="textarea mono mt-2 min-h-[220px]" value={frontendCode} onChange={(e) => setFrontendCode(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-bold text-slate-200">package.json</label>
                <textarea className="textarea mono mt-2 min-h-[150px]" value={packageJson} onChange={(e) => setPackageJson(e.target.value)} />
              </div>
            </div>
          )}

          {module === "api" && (
            <div className="mt-5 space-y-4 rounded-2xl border border-cyan/20 bg-cyan/10 p-4">
              <div>
                <p className="text-sm font-black text-white">Optional API URL/config hints</p>
                <p className="mt-1 text-xs text-slate-300">validates public URL safety and scans pasted API config/code for CORS, auth, rate-limit, docs exposure, hardcoded secrets, webhook signature, and debug risks. No fuzzing or auth bypass.</p>
              </div>
              <div>
                <label className="text-sm font-bold text-slate-200">API base URL</label>
                <input className="input mt-2" value={apiBaseUrl} onChange={(e) => setApiBaseUrl(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-bold text-slate-200">API config/code snippet</label>
                <textarea className="textarea mono mt-2 min-h-[220px]" value={apiCode} onChange={(e) => setApiCode(e.target.value)} />
              </div>
            </div>
          )}

          {module !== "contract" && module !== "website" && (
            <div className="mt-5">
              <label className="text-sm font-bold text-slate-200">{module === "wallet" ? "Wallet flow notes" : module === "admin-opsec" ? "Founder/admin OpSec notes" : "Reviewer notes / architecture notes"}</label>
              <textarea className="textarea mt-2 min-h-[130px]" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={module === "wallet" ? "Describe approval, spender, permit/signature, chain, mint/claim, and wallet prompt behavior." : module === "admin-opsec" ? "Describe owner wallet, multisig, timelock, treasury, private key policy, admin accounts, and incident plan." : "Add wallet flow, API auth model, deployment notes, admin endpoints, or known launch concerns."} />
            </div>
          )}

          {module === "contract" || module === "website" ? (
            <div className="mt-5">
              <label className="text-sm font-bold text-slate-200">{module === "website" ? "Website / dApp URL" : "Solidity code"}</label>
              {module === "website" ? (
                <input className="input mt-2" value={input} onChange={(e) => setInput(e.target.value)} />
              ) : (
                <textarea className="textarea mono mt-2 min-h-[420px]" value={input} onChange={(e) => setInput(e.target.value)} />
              )}
            </div>
          ) : (
            <div className="mt-5 space-y-3">
              <button type="button" className="btn-secondary w-full" onClick={loadChecklist}>Load checklist</button>
              {(checklist.length ? checklist : fallbackChecklist(module)).map((item, idx) => (
                <div key={item.key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-sm font-bold text-white">{item.label}</p>
                  <select
                    className="select mt-2"
                    value={item.answer}
                    onChange={(e) => {
                      const next = [...(checklist.length ? checklist : fallbackChecklist(module))];
                      next[idx] = { ...next[idx], answer: e.target.value as ChecklistItem["answer"] };
                      setChecklist(next);
                    }}
                  >
                    <option value="yes">Yes / Ready</option>
                    <option value="no">No / Missing</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>
              ))}
            </div>
          )}

          {module === "website" && (
            <div className="mt-5 rounded-2xl border border-cyan/20 bg-cyan/10 p-4 text-sm text-slate-200">
              <p className="font-black text-white">Passive-only safety mode</p>
              <p className="mt-2 text-slate-300">This scanner uses safe GET/HEAD checks only, validates redirects, blocks private/internal IP ranges, limits response size, and never runs exploit payloads or brute-force crawling. Future deep scan requires ownership verification via DNS TXT or /.well-known token.</p>
            </div>
          )}

          <label className="mt-5 flex items-start gap-3 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
            <input type="checkbox" className="mt-1" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} />
            <span>I own this project or have authorization to run this preliminary passive/checklist/code-submitted review. I understand this is not exploit testing or a certified audit.</span>
          </label>

          <button type="button" disabled={loading || !authorized} className="btn-primary mt-5 w-full disabled:cursor-not-allowed disabled:opacity-50" onClick={runScan}>
            {loading ? "Scanning..." : "Run Preliminary Review"}
          </button>
          {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-100">{error}</p>}

          {module === "contract" && rules.length > 0 && (
            <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm font-black text-white">Active rule coverage: {rules.length} rules</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {Array.from(new Set(rules.map((rule) => rule.category))).map((category) => <span key={category} className="badge">{category}</span>)}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-5">
          {result ? (
            <>
              <ScoreCard score={result.module_score.score} label={result.module_score.risk_label} />
              <div className="card p-6">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div>
                    <p className="text-sm text-slate-400">Report ID</p>
                    <p className="mono break-all text-sm text-cyan">{result.report_id}</p>
                    <p className="mt-2 text-xs text-slate-500">Engine: {result.engine_version || "web3guard-rule-engine"} · Hash: {result.input_hash || "n/a"}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" disabled={reportLoading} onClick={generateLaunchReport} className="btn-secondary disabled:opacity-50">
                      {reportLoading ? "Generating..." : "Generate Final Report"}
                    </button>
                    <button type="button" disabled={saveLoading} onClick={saveResultToDashboard} className="btn-secondary disabled:opacity-50">
                      {saveLoading ? "Saving..." : "Save Scan"}
                    </button>
                    {launchReport && (
                      <button type="button" disabled={saveLoading} onClick={saveReportToDashboard} className="btn-secondary disabled:opacity-50">Save Report</button>
                    )}
                    <a href="/contact" className="btn-primary">Request Paid Review</a>
                  </div>
                </div>

                <SeveritySummary result={result} />
                {module === "website" && <WebsiteEvidence result={result} />}
                {(module === "dapp" || module === "api") && <DappApiEvidence result={result} />}
                {(module === "wallet" || module === "admin-opsec") && <WalletAdminEvidence result={result} />}
                <PriorityActions actions={result.priority_actions || []} />

                <div className="mt-6 space-y-6">
                  {result.findings.length === 0 ? (
                    <p className="rounded-2xl border border-green-400/30 bg-green-500/10 p-4 text-green-100">No major rule findings detected in this preliminary module.</p>
                  ) : (
                    severityOrder.map((severity) => groupedFindings[severity]?.length ? (
                      <section key={severity}>
                        <h2 className="mb-3 text-sm font-black uppercase tracking-[0.2em] text-slate-400">{severity} findings</h2>
                        <div className="space-y-4">{groupedFindings[severity].map((finding) => <FindingCard key={finding.id} finding={finding} />)}</div>
                      </section>
                    ) : null)
                  )}
                </div>
                <p className="mt-5 text-sm text-amber-100">{result.disclaimer}</p>
                {saveMessage && <p className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">{saveMessage}</p>}
              </div>
              {launchReport && <ReportPreview report={launchReport} />}
            </>
          ) : (
            <div className="card p-8">
              <p className="text-xl font-black">Result + report preview</p>
              <p className="mt-3 text-slate-400">Run a scan to see findings, then generate the final combined report with weighted score, coverage confidence, report hash, export buttons, priority actions, limitations, and paid package recommendation.</p>
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="text-3xl font-black">100</p><p className="text-xs text-slate-400">Base score</p></div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="text-3xl font-black">AI</p><p className="text-xs text-slate-400">Optional provider</p></div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="text-3xl font-black">PDF</p><p className="text-xs text-slate-400">Final report</p></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SeveritySummary({ result }: { result: ScanResponse }) {
  const breakdown = result.severity_breakdown;
  if (!breakdown) return null;
  return (
    <div className="mt-6 grid gap-3 sm:grid-cols-5">
      {severityOrder.map((severity) => (
        <div key={severity} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">{severity}</p>
          <p className="mt-1 text-2xl font-black text-white">{breakdown[severity] || 0}</p>
        </div>
      ))}
    </div>
  );
}

function PriorityActions({ actions }: { actions: string[] }) {
  if (!actions.length) return null;
  return (
    <div className="mt-6 rounded-2xl border border-cyan/20 bg-cyan/10 p-4">
      <p className="text-sm font-black text-white">Priority fix actions</p>
      <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-200">
        {actions.map((action) => <li key={action}>{action}</li>)}
      </ol>
    </div>
  );
}


function WalletAdminEvidence({ result }: { result: ScanResponse }) {
  const metadata = (result.scan_metadata || {}) as Record<string, unknown>;
  const safety = (metadata.safety_controls || {}) as Record<string, unknown>;
  const readiness = (metadata.readiness_map || {}) as Record<string, Record<string, number>>;
  return (
    <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-black text-white">evidence</p>
          <p className="mt-1 text-xs text-slate-400">Checklist + notes hints only. No wallet connection, no transaction signing, no private-key collection, no seed phrase collection.</p>
        </div>
        <span className="badge">{String(metadata.mode || "checklist_plus_notes_hints")}</span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <MiniEvidence label="Notes provided" value={String(metadata.notes_provided ?? false)} />
        <MiniEvidence label="No signing" value={String(safety.no_transaction_signing ?? true)} />
        <MiniEvidence label="No key collection" value={String(safety.no_private_key_collection ?? true)} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {Object.entries(readiness).map(([name, rawValue]) => {
          const value = rawValue as Record<string, number | undefined>;
          return (
            <div key={name} className="rounded-2xl border border-white/10 bg-black/20 p-3">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{name.replaceAll("_", " ")}</p>
              <p className="mt-2 text-sm text-slate-300">Ready: <span className="text-green-200">{value.ready || 0}</span> · Missing: <span className="text-red-200">{value.missing || 0}</span> · Unknown: <span className="text-amber-100">{value.unknown || 0}</span> / {value.total || 0}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DappApiEvidence({ result }: { result: ScanResponse }) {
  const metadata = (result.scan_metadata || {}) as Record<string, unknown>;
  const safety = (metadata.safety_controls || {}) as Record<string, unknown>;
  const docsHints = asStringArray(metadata.docs_endpoint_hints);
  return (
    <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-black text-white">evidence</p>
          <p className="mt-1 text-xs text-slate-400">Checklist + optional static hints only. No exploit execution, package install, fuzzing, or auth bypass.</p>
        </div>
        <span className="badge">{String(metadata.mode || "static_hints")}</span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <MiniEvidence label="Code provided" value={String(metadata.code_provided ?? metadata.api_code_provided ?? false)} />
        <MiniEvidence label="Package/API URL" value={String(metadata.package_json_provided ?? metadata.api_url_provided ?? false)} />
        <MiniEvidence label="No exploit" value={String(safety.no_exploit_execution ?? safety.no_payload_testing ?? true)} />
      </div>
      {Boolean(metadata.validated_api_base) && (
        <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Validated API base</p>
          <p className="mt-2 break-all text-sm text-cyan">{String(metadata.validated_api_base)}</p>
        </div>
      )}
      {docsHints.length > 0 && <EvidenceList title="Docs endpoint hints for manual owner check" items={docsHints} empty="No endpoint hints." />}
    </div>
  );
}

function WebsiteEvidence({ result }: { result: ScanResponse }) {
  const metadata = (result.scan_metadata || {}) as Record<string, unknown>;
  const safety = (metadata.safety_controls || {}) as Record<string, unknown>;
  const htmlEvidence = (metadata.html_evidence || {}) as Record<string, unknown>;
  const headersMissing = asStringArray(metadata.headers_missing);
  const headersPresent = asStringArray(metadata.headers_present);
  const pathResults = Array.isArray(metadata.limited_path_results) ? metadata.limited_path_results as Array<Record<string, unknown>> : [];
  const scripts = Array.isArray(htmlEvidence.external_scripts) ? htmlEvidence.external_scripts as Array<Record<string, unknown>> : [];

  return (
    <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-black text-white">Passive website evidence</p>
          <p className="mt-1 text-xs text-slate-400">Final URL, response status, headers, scripts, and limited path hints captured without aggressive scanning.</p>
        </div>
        <span className="badge">{String(safety.mode || "passive_only")}</span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <MiniEvidence label="Status" value={String(metadata.status_code || "n/a")} />
        <MiniEvidence label="Response" value={`${String(metadata.response_time_ms || "n/a")} ms`} />
        <MiniEvidence label="External scripts" value={String(htmlEvidence.external_script_count ?? "0")} />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Final URL</p>
          <p className="mt-2 break-all text-sm text-cyan">{String(metadata.final_url || metadata.requested_url || "n/a")}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Robots / sitemap</p>
          <p className="mt-2 text-sm text-slate-300">robots.txt: {String(metadata.robots_status || "n/a")} · sitemap.xml: {String(metadata.sitemap_status || "n/a")}</p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <EvidenceList title="Present security headers" items={headersPresent} empty="No target headers detected." />
        <EvidenceList title="Missing security headers" items={headersMissing} empty="No target headers missing." />
      </div>

      {pathResults.length > 0 && (
        <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Limited sensitive path hints</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {pathResults.slice(0, 12).map((item) => (
              <p key={String(item.path)} className="rounded-xl bg-white/[0.03] px-3 py-2 text-xs text-slate-300">
                <span className="text-slate-100">{String(item.path)}</span> → {String(item.status_code || item.error || "n/a")}
              </p>
            ))}
          </div>
        </div>
      )}

      {scripts.length > 0 && (
        <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">External script domains</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {Array.from(new Set(scripts.map((item) => String(item.domain || "unknown")))).slice(0, 14).map((domain) => <span key={domain} className="badge">{domain}</span>)}
          </div>
        </div>
      )}
    </div>
  );
}

function MiniEvidence({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-black text-white">{value}</p>
    </div>
  );
}

function EvidenceList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
      <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{title}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.length ? items.map((item) => <span key={item} className="badge">{item}</span>) : <span className="text-xs text-slate-500">{empty}</span>}
      </div>
    </div>
  );
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}

function FindingCard({ finding }: { finding: Finding }) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-wrap items-center gap-3">
        <SeverityBadge severity={finding.severity} />
        <h3 className="font-black text-white">{finding.title}</h3>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">{finding.description}</p>
      <div className="mt-3 grid gap-2 text-xs text-slate-400 sm:grid-cols-3">
        <p><strong className="text-slate-200">Rule:</strong> {finding.rule_id || "n/a"}</p>
        <p><strong className="text-slate-200">Confidence:</strong> {finding.confidence}</p>
        <p><strong className="text-slate-200">Function:</strong> {finding.affected_function || "n/a"}</p>
      </div>
      {finding.affected_line && <p className="mt-2 text-xs text-slate-400"><strong className="text-slate-200">Line:</strong> {finding.affected_line}</p>}
      {finding.affected_code && <pre className="mono mt-3 overflow-x-auto rounded-2xl border border-white/10 bg-black/40 p-3 text-xs leading-6 text-cyan"><code>{finding.affected_code}</code></pre>}
      <p className="mt-3 text-sm text-slate-400"><strong className="text-slate-200">Business impact:</strong> {finding.business_impact}</p>
      <p className="mt-2 text-sm text-slate-400"><strong className="text-slate-200">Developer explanation:</strong> {finding.developer_explanation}</p>
      <p className="mt-2 text-sm text-slate-400"><strong className="text-slate-200">Fix direction:</strong> {finding.recommendation}</p>
      {finding.references?.length ? <div className="mt-3 flex flex-wrap gap-2">{finding.references.map((reference) => <span key={reference} className="badge">{reference}</span>)}</div> : null}
    </article>
  );
}

function groupFindingsBySeverity(findings: Finding[]): Record<Severity, Finding[]> {
  return severityOrder.reduce((acc, severity) => {
    acc[severity] = findings.filter((finding) => finding.severity === severity);
    return acc;
  }, {} as Record<Severity, Finding[]>);
}

const sampleContract = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract UnsafeSampleToken {
    address public owner;
    mapping(address => uint256) public balanceOf;

    constructor() { owner = msg.sender; }

    function mint(address to, uint256 amount) public {
        balanceOf[to] += amount;
    }

    function withdraw(address payable to, uint256 amount) public {
        require(tx.origin == owner, "not owner");
        to.call{value: amount}("");
        balanceOf[msg.sender] -= amount;
    }
}`;

const sampleDappCode = `const config = {
  rpcUrl: "https://eth-mainnet.g.alchemy.com/v2/unsafe-placeholder-key",
  contractAddress: "0x1111111111111111111111111111111111111111",
  NEXT_PUBLIC_ADMIN_API_KEY: "unsafe_public_placeholder_key"
};

export function MintButton() {
  const autoConnect = true;
  const allowance = ethers.constants.MaxUint256;
  return <div dangerouslySetInnerHTML={{ __html: window.location.hash }} />;
}`;

const samplePackageJson = `{
  "dependencies": {
    "next": "14.2.0",
    "ethers": "^6.13.0",
    "web3modal": "^1.9.12",
    "@walletconnect/client": "^1.8.0"
  }
}`;

const sampleApiCode = `from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

JWT_SECRET = "unsafe-hardcoded-secret"
app = FastAPI(debug=True)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)

@app.post("/webhook/razorpay")
def webhook(payload: dict):
    return {"ok": True}

@app.get("/users/{id}")
def user_detail(id: str):
    return {"id": id}
`;


const sampleWalletNotes = `Mint page uses WalletConnect.
User clicks claim button and the app asks for MaxUint256 unlimited approval.
Permit2 may be used later for gasless approvals.
Spender address is not currently shown in the confirmation UI.
Some users reported wallet prompt on page load during beta.
Need chain mismatch handling for Polygon vs Ethereum.`;

const sampleAdminNotes = `Current owner is a single EOA owner and owner is deployer.
No multisig and no timelock yet.
Treasury same wallet as deployer treasury.
One private key was stored in .env during testing and shared in Telegram once.
MFA missing on registrar and hosting account.
Upgradeable proxy planned for next release.
No incident response or pause plan yet.`;

function fallbackChecklist(module: string): ChecklistItem[] {
  const map: Record<string, ChecklistItem[]> = {
    dapp: [
      { key: "secrets", label: "No frontend-exposed secrets/API keys", answer: "unknown" },
      { key: "chain_check", label: "dApp checks chain ID before transaction", answer: "unknown" },
      { key: "tx_preview", label: "Transaction preview clearly shows token/amount/spender", answer: "unknown" },
      { key: "dangerous_html", label: "No unsafe HTML rendering in sensitive pages", answer: "unknown" },
      { key: "auto_connect", label: "Wallet does not auto-connect or auto-trigger transactions on page load", answer: "unknown" },
      { key: "approval_warning", label: "Unlimited approvals/setApprovalForAll are clearly warned and minimized", answer: "unknown" },
      { key: "verified_contract", label: "UI shows verified contract address, network, and explorer link", answer: "unknown" },
      { key: "dependency_review", label: "Frontend dependencies are reviewed before launch", answer: "unknown" }
    ],
    api: [
      { key: "rate_limit", label: "API has rate limiting", answer: "unknown" },
      { key: "auth", label: "Sensitive API routes require auth + authorization", answer: "unknown" },
      { key: "cors", label: "CORS is restricted to trusted origins", answer: "unknown" },
      { key: "webhook_signature", label: "Webhooks verify signatures", answer: "unknown" },
      { key: "docs_exposure", label: "Public docs/admin/debug endpoints are intentionally scoped", answer: "unknown" },
      { key: "error_masking", label: "Errors do not leak stack traces, secrets, or internal IDs", answer: "unknown" },
      { key: "input_validation", label: "Request validation exists for all public endpoints", answer: "unknown" },
      { key: "audit_logs", label: "Admin/payment/security actions are audit logged", answer: "unknown" },
      { key: "idor_review", label: "BOLA/IDOR object-level authorization is reviewed", answer: "unknown" }
    ],
    wallet: [
      { key: "domain_verify", label: "WalletConnect/domain verification is planned and domain matches official links", answer: "unknown" },
      { key: "chain_check", label: "Wallet flow checks chain ID before transaction/signature", answer: "unknown" },
      { key: "spender_display", label: "Approval spender/operator address is clearly displayed", answer: "unknown" },
      { key: "amount_preview", label: "Transaction preview shows token, amount, recipient/spender, contract, and chain", answer: "unknown" },
      { key: "allowance_warning", label: "Unlimited approvals are minimized and clearly warned", answer: "unknown" },
      { key: "set_approval_for_all", label: "setApprovalForAll/NFT operator approvals have a strong warning", answer: "unknown" },
      { key: "permit_warning", label: "Permit/Permit2 signatures are explained clearly", answer: "unknown" },
      { key: "blind_signing", label: "Blind signing/raw opaque signatures are avoided or clearly flagged", answer: "unknown" },
      { key: "typed_data", label: "Signature flow uses typed/human-readable data where possible", answer: "unknown" },
      { key: "session_disconnect", label: "Users can disconnect wallet sessions and understand persistence", answer: "unknown" },
      { key: "verified_contract", label: "UI shows verified contract address and explorer link", answer: "unknown" },
      { key: "no_auto_prompt", label: "Wallet prompts happen only after explicit user action", answer: "unknown" }
    ],
    "admin-opsec": [
      { key: "multisig", label: "Owner/admin wallet uses multisig for critical actions", answer: "unknown" },
      { key: "timelock", label: "Critical changes use timelock where needed", answer: "unknown" },
      { key: "role_separation", label: "Owner, pauser, minter, upgrader, deployer, and treasury roles are separated", answer: "unknown" },
      { key: "emergency_pause", label: "Emergency pause and recovery process exists", answer: "unknown" },
      { key: "upgrade_admin", label: "Proxy/upgrade admin is controlled by multisig/timelock and documented", answer: "unknown" },
      { key: "treasury_separate", label: "Treasury wallet is separate from deployer/admin wallet", answer: "unknown" },
      { key: "hardware_wallet", label: "Founder/admin signers use hardware wallets or secure custody", answer: "unknown" },
      { key: "private_key_policy", label: "Private key/seed phrase storage policy exists and is enforced", answer: "unknown" },
      { key: "mfa", label: "Admin tools, GitHub, registrar, hosting, and email use strong MFA", answer: "unknown" },
      { key: "audit_logs", label: "Admin/payment/security actions are audit logged", answer: "unknown" },
      { key: "signer_rotation", label: "Signer rotation and team offboarding process exists", answer: "unknown" },
      { key: "incident_response", label: "Incident response plan exists", answer: "unknown" },
      { key: "backup_admin", label: "Safe backup admin/recovery process exists", answer: "unknown" }
    ]
  };
  return map[module] || [];
}
