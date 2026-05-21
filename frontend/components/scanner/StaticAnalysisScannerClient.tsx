"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

type ToolStatus = {
  enabled_by_env: boolean;
  installed: boolean;
  path?: string | null;
  will_run: boolean;
  note: string;
};

type StaticStatus = {
  static_analysis_enabled: boolean;
  default_timeout_seconds: number;
  tools: Record<string, ToolStatus>;
  safety_controls: Record<string, boolean>;
};

const sampleSolidity = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract StaticAnalysisRiskExample {
    address public owner;
    constructor(){ owner = msg.sender; }

    function withdraw(address payable to) external {
        require(tx.origin == owner, "not owner");
        to.call{value: address(this).balance}("");
    }

    function destroy(address payable to) external {
        require(msg.sender == owner, "not owner");
        selfdestruct(to);
    }
}`;

export function StaticAnalysisScannerClient() {
  const [status, setStatus] = useState<StaticStatus | null>(null);
  const [projectName, setProjectName] = useState("Static Analysis Project");
  const [fileName, setFileName] = useState("Contract.sol");
  const [code, setCode] = useState(sampleSolidity);
  const [tools, setTools] = useState<Record<string, boolean>>({ slither: true, aderyn: false, semgrep: true });
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    apiGet<StaticStatus>("/scan/static-analysis/status").then(setStatus).catch(() => setStatus(null));
  }, []);

  async function runScan() {
    setLoading(true);
    setError(null);
    setResult(null);
    setSaveMessage(null);
    try {
      const selectedTools = Object.entries(tools).filter(([, enabled]) => enabled).map(([tool]) => tool);
      const data = await apiPost<ScanResponse>("/scan/static-analysis", {
        project_name: projectName,
        file_name: fileName,
        solidity_code: code,
        tools: selectedTools,
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Static analysis failed");
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
        name: projectName || "Static Analysis Scan",
        project_type: "Static analysis",
        description: "Created from static-analysis scanner. Only real installed/enabled tool outputs are treated as evidence.",
      }, { headers });
      await apiPost("/scan-history", {
        user_id: userId,
        project_id: project.project.id,
        module: "static_analysis",
        project_name: projectName,
        score: result.module_score.score,
        risk_label: result.module_score.risk_label,
        report_id: result.report_id,
        input_hash: result.input_hash,
        findings_count: result.findings.length,
        critical_high_count: result.findings.filter((finding) => finding.severity === "critical" || finding.severity === "high").length,
        status: "saved_from_static_analysis_scanner",
        payload: result,
      }, { headers });
      setSaveMessage("Static-analysis scan saved to dashboard as a real record. It is not a certified audit.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save static-analysis scan");
    } finally {
      setSaveLoading(false);
    }
  }

  const toolRuns = (result?.scan_metadata?.tool_runs || {}) as Record<string, unknown>;

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">• Real tool runner</p>
        <h1 className="mt-3 text-3xl font-black sm:text-5xl">Slither / Aderyn / Semgrep Static Analysis</h1>
        <p className="mt-4 text-slate-400">
          Runs real external static-analysis tools only when they are installed and enabled on the backend. If a tool is missing or disabled, Web3Guard AI shows a tool-status finding instead of fake vulnerabilities.
        </p>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-bold text-slate-200">Project name
              <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
            </label>
            <label className="block text-sm font-bold text-slate-200">File name
              <input className="input mt-2" value={fileName} onChange={(event) => setFileName(event.target.value)} />
            </label>
          </div>

          <div className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4">
            <p className="text-sm font-black text-white">Tool status</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              {(["slither", "aderyn", "semgrep"] as const).map((tool) => {
                const info = status?.tools?.[tool];
                return (
                  <label key={tool} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm">
                    <span className="flex items-center gap-2 font-bold text-white">
                      <input type="checkbox" checked={tools[tool]} onChange={(event) => setTools((current) => ({ ...current, [tool]: event.target.checked }))} />
                      {tool}
                    </span>
                    <span className="mt-2 block text-xs text-slate-400">Installed: {info?.installed ? "yes" : "no"}</span>
                    <span className="block text-xs text-slate-400">Will run: {info?.will_run ? "yes" : "no"}</span>
                  </label>
                );
              })}
            </div>
            <p className="mt-3 text-xs text-amber-100">STATIC_ANALYSIS_ENABLED must be true and the tool must be installed for real tool execution.</p>
          </div>

          <label className="mt-5 block text-sm font-bold text-slate-200">Solidity source
            <textarea className="textarea mono mt-2 min-h-[360px]" value={code} onChange={(event) => setCode(event.target.value)} />
          </label>

          <div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
            <label className="flex gap-3">
              <input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} />
              <span>I own this code or have authorization to run static analysis on it.</span>
            </label>
            <label className="flex gap-3">
              <input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} />
              <span>I understand missing tools will not produce fake findings or certified-audit claims.</span>
            </label>
          </div>

          <button className="btn-primary mt-5 w-full" disabled={loading || !authorized || !realOnly || !code} onClick={runScan}>
            {loading ? "Running real tool checks..." : "Run Static Analysis"}
          </button>
          {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
        </div>

        <div className="space-y-5">
          {!result && (
            <div className="card p-6">
              <p className="text-lg font-black text-white">Real-only execution model</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                <li>• No fake Slither/Aderyn/Semgrep results.</li>
                <li>• No dependency install, repo clone, private key collection, or contract execution.</li>
                <li>• Temp workspace is deleted after the scan by default.</li>
                <li>• Use Docker/isolated worker before enabling this in production.</li>
              </ul>
            </div>
          )}

          {result && (
            <>
              <ScoreCard label={result.module_score.risk_label} score={result.module_score.score} />
              <div className="card p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-400">Report ID</p>
                    <p className="mt-1 font-bold text-white">{result.report_id}</p>
                    <p className="mt-1 text-sm text-slate-500">Engine: {result.engine_version}</p>
                  </div>
                  <button className="btn-secondary" disabled={saveLoading} onClick={saveToDashboard}>{saveLoading ? "Saving..." : "Save to Dashboard"}</button>
                </div>
                {saveMessage && <p className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">{saveMessage}</p>}
              </div>

              <div className="card p-6">
                <p className="text-lg font-black text-white">Tool run evidence</p>
                <pre className="mono mt-3 max-h-80 overflow-auto rounded-2xl bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(toolRuns, null, 2)}</pre>
              </div>

              <div className="card p-6">
                <p className="text-lg font-black text-white">Findings & tool status</p>
                <div className="mt-4 space-y-3">
                  {result.findings.map((finding) => (
                    <div key={finding.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <SeverityBadge severity={finding.severity} />
                        <span className="text-xs text-slate-500">{finding.source}</span>
                      </div>
                      <p className="mt-3 font-bold text-white">{finding.title}</p>
                      <p className="mt-2 text-sm text-slate-400">{finding.description}</p>
                      {finding.affected_line && <p className="mt-2 text-xs text-slate-500">Line: {finding.affected_line}</p>}
                      {finding.affected_code && <pre className="mono mt-3 overflow-x-auto rounded-xl bg-black/40 p-3 text-xs text-slate-300">{finding.affected_code}</pre>}
                      <p className="mt-3 text-sm text-cyan">Fix direction: {finding.recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
