"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { UnifiedUrlScanResponse } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

const moduleOrder = ["website", "dapp", "api", "contract", "wallet", "admin_opsec", "github"];

function statusClass(status: string) {
  const lowered = status.toLowerCase();
  if (lowered.startsWith("live")) return "border-emerald-400/30 bg-emerald-500/10 text-emerald-100";
  if (lowered.includes("manual") || lowered.includes("input")) return "border-amber-400/30 bg-amber-500/10 text-amber-100";
  if (lowered.includes("not assessed")) return "border-slate-400/30 bg-slate-500/10 text-slate-200";
  return "border-cyan/30 bg-cyan/10 text-cyan";
}

export function UnifiedUrlScannerClient() {
  const [websiteUrl, setWebsiteUrl] = useState("https://example.com");
  const [projectName, setProjectName] = useState("RAADHANEX Demo Project");
  const [projectType, setProjectType] = useState("ERC20 / dApp");
  const [chain, setChain] = useState("Polygon");
  const [contractAddress, setContractAddress] = useState("");
  const [apiBaseUrl, setApiBaseUrl] = useState("");
  const [githubRepoUrl, setGithubRepoUrl] = useState("");
  const [solidityCode, setSolidityCode] = useState("");
  const [authorized, setAuthorized] = useState(true);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<UnifiedUrlScanResponse | null>(null);

  async function runScan() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiPost<UnifiedUrlScanResponse>("/scan/unified-url", {
        website_url: websiteUrl,
        project_name: projectName,
        project_type: projectType,
        chain,
        contract_address: contractAddress || null,
        api_base_url: apiBaseUrl || null,
        github_repo_url: githubRepoUrl || null,
        solidity_code: solidityCode || null,
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unified URL scan failed");
    } finally {
      setLoading(false);
    }
  }

  async function saveUnifiedScanToDashboard() {
    if (!result) return;
    setSaveLoading(true);
    setSaveMessage(null);
    setError(null);
    try {
      const userId = await getCurrentUserId();
      const token = await getSessionToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
      const projectResponse = await apiPost<{ project: { id: string } }>("/projects", {
        user_id: userId,
        name: projectName || "Unified URL Launch Scan",
        website_url: websiteUrl,
        chain,
        contract_address: contractAddress || null,
        github_repo_url: githubRepoUrl || null,
        project_type: projectType,
        description: "Created from unified URL launch scanner. Only actually assessed modules were scored.",
      }, { headers });
      const criticalHigh = result.priority_actions?.filter((item) => item.severity === "critical" || item.severity === "high").length || 0;
      await apiPost("/scan-history", {
        user_id: userId,
        project_id: projectResponse.project.id,
        module: "unified_url",
        project_name: projectName,
        score: result.available_score ?? null,
        risk_label: result.risk_label,
        report_id: result.report_id,
        findings_count: result.module_cards.reduce((sum, card) => sum + (card.findings_count || 0), 0),
        critical_high_count: criticalHigh,
        status: "saved_from_unified_url_scanner",
        payload: result,
      }, { headers });
      setSaveMessage("Unified URL scan saved to dashboard as a real record. Missing modules remain Not assessed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save unified scan");
    } finally {
      setSaveLoading(false);
    }
  }

  const cards = result?.module_cards ? [...result.module_cards].sort((a, b) => moduleOrder.indexOf(a.module) - moduleOrder.indexOf(b.module)) : [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Phase 5.5.1 • Real-only unified URL scanner</p>
        <h1 className="mt-3 text-3xl font-black sm:text-5xl">Unified Website URL Launch Scanner</h1>
        <p className="mt-4 text-slate-400">
          Enter one public website URL and optional real inputs. The scanner will only score modules that are actually assessed. Missing contract/API/wallet/admin/GitHub inputs are marked as <strong className="text-white">Not assessed</strong>, not fake-scored.
        </p>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="card p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-bold text-slate-200">Project name
              <input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} />
            </label>
            <label className="block text-sm font-bold text-slate-200">Project type
              <input className="input mt-2" value={projectType} onChange={(e) => setProjectType(e.target.value)} />
            </label>
          </div>
          <label className="mt-4 block text-sm font-bold text-slate-200">Website / dApp URL <span className="text-red-200">*</span>
            <input className="input mt-2" value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} placeholder="https://yourproject.com" />
          </label>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-bold text-slate-200">Chain
              <input className="input mt-2" value={chain} onChange={(e) => setChain(e.target.value)} placeholder="Ethereum / Polygon / BNB" />
            </label>
            <label className="block text-sm font-bold text-slate-200">Contract address optional
              <input className="input mt-2" value={contractAddress} onChange={(e) => setContractAddress(e.target.value)} placeholder="0x..." />
            </label>
          </div>
          <label className="mt-4 block text-sm font-bold text-slate-200">API base URL optional
            <input className="input mt-2" value={apiBaseUrl} onChange={(e) => setApiBaseUrl(e.target.value)} placeholder="https://api.yourproject.com" />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-200">GitHub repo URL optional
            <input className="input mt-2" value={githubRepoUrl} onChange={(e) => setGithubRepoUrl(e.target.value)} placeholder="https://github.com/team/project" />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-200">Solidity source optional for real contract score
            <textarea className="textarea mono mt-2 min-h-[180px]" value={solidityCode} onChange={(e) => setSolidityCode(e.target.value)} placeholder="Paste Solidity source here if you want the contract module scored now." />
          </label>

          <div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
            <label className="flex gap-3">
              <input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} />
              <span>I own this project or have authorization to run passive launch-surface checks.</span>
            </label>
            <label className="flex gap-3">
              <input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} />
              <span>I understand missing modules will be marked Not assessed instead of fake-scored.</span>
            </label>
          </div>

          <button className="btn-primary mt-5 w-full" onClick={runScan} disabled={loading || !authorized || !realOnly}>
            {loading ? "Running real passive scan..." : "Run Unified URL Scan"}
          </button>
          {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
        </div>

        <div className="space-y-5">
          {!result && (
            <div className="card p-6">
              <p className="text-lg font-black text-white">Real-only behavior</p>
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                <li>• Website URL = live passive checks.</li>
                <li>• Contract address = recorded only until explorer fetch is enabled.</li>
                <li>• Solidity paste = live rule-engine contract score.</li>
                <li>• API URL = live safety validation, no fuzzing.</li>
                <li>• Wallet/admin/GitHub = no fake score without real input or integration.</li>
              </ul>
            </div>
          )}

          {result && (
            <>
              <div className="card p-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-400">Available partial score</p>
                    <p className="mt-2 text-5xl font-black text-white">{result.available_score ?? "N/A"}</p>
                    <p className="mt-2 text-sm text-slate-400">{result.risk_label}</p>
                  </div>
                  <div className="rounded-2xl border border-cyan/30 bg-cyan/10 px-4 py-3 text-sm text-cyan">
                    {result.live_module_count} live/limited module(s)
                  </div>
                </div>
                <button type="button" disabled={saveLoading} onClick={saveUnifiedScanToDashboard} className="btn-secondary mt-5 disabled:opacity-50">
                  {saveLoading ? "Saving..." : "Save to Dashboard"}
                </button>
                {saveMessage && <p className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">{saveMessage}</p>}
                <p className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3 text-sm text-slate-300">{result.realness_rule}</p>
                <p className="mt-3 text-xs text-amber-100">{result.safe_public_summary}</p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {cards.map((card) => (
                  <div key={card.module} className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h3 className="font-black text-white">{card.label}</h3>
                      <span className={`rounded-full border px-3 py-1 text-xs font-bold ${statusClass(card.status)}`}>{card.status}</span>
                    </div>
                    <p className="mt-3 text-sm text-slate-400">Score: <span className="font-bold text-white">{card.score ?? "Not assessed"}</span></p>
                    {!!card.evidence?.length && (
                      <div className="mt-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Evidence</p>
                        <ul className="mt-2 space-y-1 text-xs text-slate-300">{card.evidence.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}</ul>
                      </div>
                    )}
                    {!!card.required_input?.length && (
                      <div className="mt-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-amber-200">Needed for real score</p>
                        <ul className="mt-2 space-y-1 text-xs text-amber-50">{card.required_input.map((item) => <li key={item}>• {item}</li>)}</ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {!!result.priority_actions?.length && (
                <div className="card p-6">
                  <h3 className="text-xl font-black text-white">Priority actions from assessed modules</h3>
                  <div className="mt-4 space-y-3">
                    {result.priority_actions.slice(0, 6).map((item) => (
                      <div key={`${item.step}-${item.title}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                        <div className="flex items-center gap-3">
                          <SeverityBadge severity={item.severity} />
                          <p className="font-bold text-white">{item.title}</p>
                        </div>
                        <p className="mt-2 text-sm text-slate-400">{item.recommended_action}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="card p-6">
                <h3 className="text-xl font-black text-white">Blocked fake claims</h3>
                <ul className="mt-4 space-y-2 text-sm text-slate-300">
                  {result.blocked_claims.map((claim) => <li key={claim}>• {claim}</li>)}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
