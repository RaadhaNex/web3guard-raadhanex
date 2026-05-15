"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { ScanResponse } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { ScoreCard } from "@/components/ui/ScoreCard";

type StructureSummary = {
  total_files_seen?: number;
  solidity_count?: number;
  package_json_count?: number;
  env_like_count?: number;
  config_count?: number;
  api_like_count?: number;
  frontend_like_count?: number;
  deployment_script_count?: number;
  solidity_files?: string[];
  package_json_files?: string[];
  env_like_files?: string[];
  api_like_files?: string[];
  frontend_like_files?: string[];
};

function asSummary(value: unknown): StructureSummary {
  return typeof value === "object" && value !== null ? value as StructureSummary : {};
}

function metadataValue(result: ScanResponse | null, key: string): unknown {
  if (!result?.scan_metadata) return null;
  return result.scan_metadata[key];
}

export function GitHubRepoScannerClient() {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [projectName, setProjectName] = useState("GitHub Project");
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  async function runScan() {
    setLoading(true);
    setError(null);
    setResult(null);
    setSaveMessage(null);
    try {
      const data = await apiPost<ScanResponse>("/scan/github-repo", {
        repo_url: repoUrl,
        project_name: projectName,
        branch: branch || null,
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub repo scan failed");
    } finally {
      setLoading(false);
    }
  }

  async function saveToDashboard() {
    if (!result) return;
    setSaveLoading(true);
    setError(null);
    setSaveMessage(null);
    try {
      const userId = await getCurrentUserId();
      const token = await getSessionToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
      const project = await apiPost<{ project: { id: string } }>("/projects", {
        user_id: userId,
        name: projectName || "GitHub Repo Scan",
        github_repo_url: repoUrl,
        description: "Created from Phase 11 GitHub public repo scanner. Only fetched public evidence was scored.",
      }, { headers });
      await apiPost("/scan-history", {
        user_id: userId,
        project_id: project.project.id,
        module: "github",
        project_name: projectName,
        score: result.module_score.score,
        risk_label: result.module_score.risk_label,
        report_id: result.report_id,
        input_hash: result.input_hash,
        findings_count: result.findings.length,
        critical_high_count: result.findings.filter((finding) => finding.severity === "critical" || finding.severity === "high").length,
        status: "saved_from_github_repo_scanner",
        payload: result,
      }, { headers });
      setSaveMessage("GitHub repo scan saved to dashboard as a real scan record.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save GitHub scan");
    } finally {
      setSaveLoading(false);
    }
  }

  const summary = asSummary(metadataValue(result, "structure_summary"));
  const repo = metadataValue(result, "repo") as { url?: string; scanned_branch?: string } | null;
  const limits = metadataValue(result, "limits") as Record<string, unknown> | null;
  const safety = metadataValue(result, "safety_controls") as Record<string, unknown> | null;

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Phase 11 • Real read-only repo scanner</p>
        <h1 className="mt-3 text-3xl font-black sm:text-5xl">GitHub Repository Launch Scanner</h1>
        <p className="mt-4 text-slate-400">
          Scan a public GitHub repo with safe read-only GitHub API/raw file checks. It detects Solidity files, package.json, frontend/API/config/deploy hints, and secret-hygiene risks. It does not clone, execute, install packages, or fake Slither/Aderyn output.
        </p>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6">
          <label className="block text-sm font-bold text-slate-200">Project name
            <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-200">Public GitHub repo URL <span className="text-red-200">*</span>
            <input className="input mt-2" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/owner/repo" />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-200">Branch optional
            <input className="input mt-2" value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="main / develop / leave empty for default branch" />
          </label>

          <div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
            <label className="flex gap-3">
              <input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} />
              <span>I own this repo/project or have authorization to review this public repository.</span>
            </label>
            <label className="flex gap-3">
              <input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} />
              <span>I understand this is read-only static analysis; missing deep tools are not fake-scored.</span>
            </label>
          </div>

          <button className="btn-primary mt-5 w-full" onClick={runScan} disabled={loading || !authorized || !realOnly || !repoUrl}>
            {loading ? "Scanning public repo evidence..." : "Run GitHub Repo Scan"}
          </button>
          {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
        </div>

        <div className="space-y-5">
          {!result && (
            <div className="card p-6">
              <p className="text-lg font-black text-white">Real-only behavior</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                <li>• Uses GitHub API/tree and selected raw public files.</li>
                <li>• Does not clone, execute, install dependencies, or run npm audit.</li>
                <li>• Solidity files get limited local rule-engine checks when fetched.</li>
                <li>• Slither/Aderyn/Mythril remain not enabled until later real integration phases.</li>
              </ul>
            </div>
          )}

          {result && (
            <>
              <ScoreCard label={result.module_score.risk_label} score={result.module_score.score} />
              <div className="card p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-400">Repo</p>
                    <p className="mt-1 break-all font-bold text-white">{repo?.url || repoUrl}</p>
                    <p className="mt-1 text-sm text-slate-500">Branch: {repo?.scanned_branch || branch || "default"}</p>
                  </div>
                  <button type="button" className="btn-secondary" disabled={saveLoading} onClick={saveToDashboard}>{saveLoading ? "Saving..." : "Save to Dashboard"}</button>
                </div>
                {saveMessage && <p className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">{saveMessage}</p>}
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {[
                  ["Files seen", summary.total_files_seen],
                  ["Solidity", summary.solidity_count],
                  ["package.json", summary.package_json_count],
                  ["Env-like", summary.env_like_count],
                  ["Frontend", summary.frontend_like_count],
                  ["API-like", summary.api_like_count],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
                    <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
                    <p className="mt-2 text-3xl font-black text-white">{String(value ?? 0)}</p>
                  </div>
                ))}
              </div>

              <div className="card p-6">
                <p className="text-lg font-black text-white">Findings</p>
                <div className="mt-4 space-y-3">
                  {result.findings.length === 0 && <p className="text-sm text-slate-400">No findings were generated from fetched public evidence.</p>}
                  {result.findings.slice(0, 14).map((finding) => (
                    <div key={finding.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <SeverityBadge severity={finding.severity} />
                        <span className="text-xs text-slate-500">{finding.source}</span>
                      </div>
                      <p className="mt-3 font-bold text-white">{finding.title}</p>
                      <p className="mt-2 text-sm text-slate-400">{finding.description}</p>
                      {finding.affected_code && <pre className="mono mt-3 overflow-x-auto rounded-xl bg-black/40 p-3 text-xs text-slate-300">{finding.affected_code}</pre>}
                      <p className="mt-3 text-sm text-cyan">Fix direction: {finding.recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <div className="card p-6">
                  <p className="font-black text-white">Safety controls</p>
                  <pre className="mono mt-3 overflow-x-auto rounded-2xl bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(safety, null, 2)}</pre>
                </div>
                <div className="card p-6">
                  <p className="font-black text-white">Limits</p>
                  <pre className="mono mt-3 overflow-x-auto rounded-2xl bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(limits, null, 2)}</pre>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
