"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { StatusPill } from "@/components/ui/StatusPill";

type ToolStatus = {
  enabled_by_env: boolean;
  installed: boolean;
  path?: string | null;
  will_run: boolean;
  note: string;
};

type DeepStatus = {
  deep_analysis_enabled: boolean;
  default_timeout_seconds: number;
  tools: Record<string, ToolStatus>;
  safety_controls: Record<string, boolean>;
  scan_depths: Record<string, string>;
  not_claimed: string[];
};

const sampleSolidity = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Phase14DeepRisk {
    mapping(address => uint256) public balances;
    address public owner;

    constructor(){ owner = msg.sender; }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "empty");
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "failed");
        balances[msg.sender] = 0;
    }
}`;

export function DeepAnalysisScannerClient() {
  const [status, setStatus] = useState<DeepStatus | null>(null);
  const [projectName, setProjectName] = useState("Phase 14 Deep Analysis Project");
  const [fileName, setFileName] = useState("Contract.sol");
  const [code, setCode] = useState(sampleSolidity);
  const [scanDepth, setScanDepth] = useState("quick");
  const [tools, setTools] = useState<Record<string, boolean>>({ mythril: true, manticore: false, echidna: false });
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [ownershipVerified, setOwnershipVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    apiGet<DeepStatus>("/scan/deep-analysis/status").then(setStatus).catch(() => setStatus(null));
  }, []);

  async function runScan() {
    setLoading(true);
    setError(null);
    setResult(null);
    setSaveMessage(null);
    try {
      const selectedTools = Object.entries(tools).filter(([, enabled]) => enabled).map(([tool]) => tool);
      const data = await apiPost<ScanResponse>("/scan/deep-analysis", {
        project_name: projectName,
        file_name: fileName,
        solidity_code: code,
        tools: selectedTools,
        scan_depth: scanDepth,
        ownership_verified: ownershipVerified,
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deep analysis failed");
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
        name: projectName || "Deep Analysis Scan",
        project_type: "Deep analysis",
        description: "Created from Phase 14 deep-analysis scanner. Only real installed/enabled tool outputs are treated as evidence.",
      }, { headers });
      await apiPost("/scan-history", {
        user_id: userId,
        project_id: project.project.id,
        module: "deep_analysis",
        project_name: projectName,
        score: result.module_score.score,
        risk_label: result.module_score.risk_label,
        report_id: result.report_id,
        input_hash: result.input_hash,
        findings_count: result.findings.length,
        critical_high_count: result.findings.filter((finding) => finding.severity === "critical" || finding.severity === "high").length,
        status: "saved_from_deep_analysis_scanner",
        payload: result,
      }, { headers });
      setSaveMessage("Deep-analysis scan saved to dashboard as a real record. It is not a certified audit.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save deep-analysis scan");
    } finally {
      setSaveLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Phase 14 · Deep analysis</p>
        <h1 className="mt-3 text-4xl font-black sm:text-5xl">Mythril / Manticore / Echidna runner with no fake output.</h1>
        <p className="mt-4 text-slate-400">This layer is disabled by default. It runs real tools only when they are installed and enabled. Missing tools become Not Run evidence, not fake vulnerabilities.</p>
      </div>

      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        {status ? Object.entries(status.tools).map(([tool, info]) => (
          <div key={tool} className="card p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-black capitalize">{tool}</h2>
              <StatusPill status={info.will_run ? "Live" : info.installed ? "Installed / Disabled" : "Not installed"} />
            </div>
            <p className="mt-3 text-sm text-slate-400">Enabled: {String(info.enabled_by_env)} · Installed: {String(info.installed)}</p>
            <p className="mt-2 break-all text-xs text-slate-500">{info.path || "No binary detected"}</p>
          </div>
        )) : <div className="card p-5 text-slate-400">Loading tool status…</div>}
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <div className="card p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-bold text-slate-300">Project name
              <input value={projectName} onChange={(e) => setProjectName(e.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-cyan" />
            </label>
            <label className="text-sm font-bold text-slate-300">File name
              <input value={fileName} onChange={(e) => setFileName(e.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-cyan" />
            </label>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-bold text-slate-300">Scan depth
              <select value={scanDepth} onChange={(e) => setScanDepth(e.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-cyan">
                <option value="quick">Quick</option>
                <option value="standard">Standard · requires ownership verified</option>
                <option value="deep">Deep · requires ownership verified</option>
              </select>
            </label>
            <div className="text-sm text-slate-400">
              <p className="font-bold text-slate-300">Selected tools</p>
              <div className="mt-2 flex flex-wrap gap-3">
                {Object.keys(tools).map((tool) => (
                  <label key={tool} className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 capitalize">
                    <input type="checkbox" checked={tools[tool]} onChange={(e) => setTools((prev) => ({ ...prev, [tool]: e.target.checked }))} className="mr-2" />
                    {tool}
                  </label>
                ))}
              </div>
            </div>
          </div>

          <label className="mt-5 block text-sm font-bold text-slate-300">Solidity code
            <textarea value={code} onChange={(e) => setCode(e.target.value)} rows={18} className="mt-2 w-full rounded-2xl border border-white/10 bg-black/40 px-4 py-3 font-mono text-sm text-white outline-none focus:border-cyan" />
          </label>

          <div className="mt-5 grid gap-3 text-sm text-slate-300">
            <label><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} className="mr-2" />I own this code or have authorization to analyze it.</label>
            <label><input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} className="mr-2" />I understand only real installed/enabled tool output will be used.</label>
            <label><input type="checkbox" checked={ownershipVerified} onChange={(e) => setOwnershipVerified(e.target.checked)} className="mr-2" />Ownership verified for standard/deep mode.</label>
          </div>

          {error && <p className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-100">{error}</p>}
          <button onClick={runScan} disabled={loading} className="btn-primary mt-5 disabled:opacity-60">{loading ? "Running deep analysis…" : "Run Deep Analysis"}</button>
        </div>

        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="text-xl font-black">Safety policy</h2>
            <ul className="mt-3 space-y-2 text-sm text-slate-400">
              <li>No private key / seed collection.</li>
              <li>No mainnet transaction signing.</li>
              <li>No repo clone or dependency install in this form.</li>
              <li>Production deep runs should move into a locked Docker worker.</li>
            </ul>
          </div>
          {status && <div className="card p-6">
            <h2 className="text-xl font-black">Deep mode rules</h2>
            {Object.entries(status.scan_depths).map(([key, value]) => <p key={key} className="mt-3 text-sm text-slate-400"><b className="text-white capitalize">{key}:</b> {value}</p>)}
          </div>}
        </div>
      </section>

      {result && (
        <section className="mt-8 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <ScoreCard score={result.module_score.score} label={result.module_score.risk_label} />
          <div className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-2xl font-black">Deep analysis result</h2>
                <p className="mt-1 text-sm text-slate-400">{result.engine_version} · Report {result.report_id}</p>
              </div>
              <button onClick={saveToDashboard} disabled={saveLoading} className="btn-secondary disabled:opacity-60">{saveLoading ? "Saving…" : "Save to Dashboard"}</button>
            </div>
            {saveMessage && <p className="mt-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">{saveMessage}</p>}
            <div className="mt-5 space-y-4">
              {result.findings.map((finding) => (
                <div key={finding.id} className="rounded-3xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <SeverityBadge severity={finding.severity} />
                    <span className="text-xs text-slate-500">{finding.source}</span>
                    <span className="text-xs text-slate-500">{finding.rule_id}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-black">{finding.title}</h3>
                  <p className="mt-2 text-sm text-slate-300">{finding.description}</p>
                  <p className="mt-3 text-sm text-slate-400"><b className="text-slate-200">Recommendation:</b> {finding.recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
