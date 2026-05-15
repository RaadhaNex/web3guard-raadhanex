"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

type ExplorerStatus = {
  etherscan_v2_enabled?: boolean;
  supported_chains?: Array<{ key: string; label: string; chain_id: string }>;
  real_only_note?: string;
  not_enabled_or_not_claimed?: string[];
};

function metadata(result: ScanResponse | null, key: string): unknown {
  return result?.scan_metadata?.[key] ?? null;
}

export function ContractAddressScannerClient() {
  const [status, setStatus] = useState<ExplorerStatus | null>(null);
  const [projectName, setProjectName] = useState("Address Scan Project");
  const [address, setAddress] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    apiGet<ExplorerStatus>("/scan/contract-address/status").then(setStatus).catch(() => setStatus(null));
  }, []);

  async function runScan() {
    setLoading(true);
    setError(null);
    setSaveMessage(null);
    setResult(null);
    try {
      const data = await apiPost<ScanResponse>("/scan/contract-address", {
        address,
        chain,
        project_name: projectName,
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Contract address scan failed");
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
        name: projectName || address,
        contract_address: address,
        chain,
        description: "Created from Phase 12 verified contract address scanner.",
      }, { headers });
      await apiPost("/scan-history", {
        user_id: userId,
        project_id: project.project.id,
        module: "contract",
        project_name: projectName,
        score: result.module_score.score,
        risk_label: result.module_score.risk_label,
        report_id: result.report_id,
        input_hash: result.input_hash,
        findings_count: result.findings.length,
        critical_high_count: result.findings.filter((finding) => finding.severity === "critical" || finding.severity === "high").length,
        status: "saved_from_contract_address_scanner",
        payload: result,
      }, { headers });
      setSaveMessage("Contract address scan saved to dashboard as a real scan record.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save contract address scan");
    } finally {
      setSaveLoading(false);
    }
  }

  const explorerRecord = metadata(result, "explorer_record") as Record<string, unknown> | null;
  const abiSummary = metadata(result, "abi_summary") as Record<string, unknown> | null;
  const sourceMetadata = metadata(result, "source_metadata") as Record<string, unknown> | null;

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Phase 12 • Verified explorer source scanner</p>
        <h1 className="mt-3 text-3xl font-black sm:text-5xl">Contract Address Scanner</h1>
        <p className="mt-4 text-slate-400">
          Fetch verified source/ABI metadata from Etherscan API V2-compatible explorer flow, then run RAADHANEX local Solidity rule checks. No private key collection, wallet signing, bytecode decompilation, or fake score when source is unavailable.
        </p>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">
            Explorer API: <span className={status?.etherscan_v2_enabled ? "text-emerald-200" : "text-amber-200"}>{status?.etherscan_v2_enabled ? "configured" : "needs ETHERSCAN_API_KEY"}</span>
          </div>
          <label className="mt-4 block text-sm font-bold text-slate-200">Project name
            <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-200">EVM contract address
            <input className="input mt-2" value={address} onChange={(event) => setAddress(event.target.value)} placeholder="0x..." />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-200">Chain
            <select className="input mt-2" value={chain} onChange={(event) => setChain(event.target.value)}>
              {(status?.supported_chains || [
                { key: "ethereum", label: "Ethereum Mainnet", chain_id: "1" },
                { key: "polygon", label: "Polygon PoS", chain_id: "137" },
                { key: "bsc", label: "BNB Smart Chain", chain_id: "56" },
              ]).map((item) => <option key={item.key} value={item.key}>{item.label} · chain {item.chain_id}</option>)}
            </select>
          </label>
          <div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
            <label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} /><span>I own this project or have authorization to review this public contract.</span></label>
            <label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} /><span>I understand this only scans verified public source; unverified source will not receive a fake code score.</span></label>
          </div>
          <button className="btn-primary mt-5 w-full" onClick={runScan} disabled={loading || !authorized || !realOnly || !address}>{loading ? "Fetching verified source..." : "Run Contract Address Scan"}</button>
          {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
          {status?.not_enabled_or_not_claimed && <ul className="mt-5 space-y-2 text-sm text-slate-400">{status.not_enabled_or_not_claimed.map((item) => <li key={item}>• {item}</li>)}</ul>}
        </div>

        <div className="space-y-5">
          {!result && <div className="card p-6"><p className="font-black text-white">Real-only behavior</p><p className="mt-3 text-sm text-slate-400">{status?.real_only_note || "A contract address scan only becomes a real code scan after verified source is fetched from explorer API."}</p></div>}
          {result && <>
            <ScoreCard label={result.module_score.risk_label} score={result.module_score.score} />
            <div className="card p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">Report</p>
                  <p className="mt-1 font-bold text-white">{result.report_id}</p>
                  <p className="mt-1 text-sm text-slate-500">Source verified: {String(metadata(result, "source_verified"))}</p>
                </div>
                <button type="button" className="btn-secondary" disabled={saveLoading} onClick={saveToDashboard}>{saveLoading ? "Saving..." : "Save to Dashboard"}</button>
              </div>
              {saveMessage && <p className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">{saveMessage}</p>}
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="card p-5"><p className="font-black text-white">Explorer metadata</p><pre className="mono mt-3 overflow-x-auto rounded-2xl bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(explorerRecord, null, 2)}</pre></div>
              <div className="card p-5"><p className="font-black text-white">ABI/source summary</p><pre className="mono mt-3 overflow-x-auto rounded-2xl bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify({ abiSummary, sourceMetadata }, null, 2)}</pre></div>
            </div>
            <div className="card p-6">
              <p className="text-lg font-black text-white">Findings</p>
              <div className="mt-4 space-y-3">
                {result.findings.length === 0 && <p className="text-sm text-slate-400">No findings generated from verified explorer source.</p>}
                {result.findings.slice(0, 16).map((finding) => <div key={finding.id} className="rounded-2xl border border-white/10 bg-black/20 p-4"><div className="flex flex-wrap items-center gap-2"><SeverityBadge severity={finding.severity} /><span className="text-xs text-slate-500">{finding.source}</span></div><p className="mt-3 font-bold text-white">{finding.title}</p><p className="mt-2 text-sm text-slate-400">{finding.description}</p>{finding.affected_code && <pre className="mono mt-3 overflow-x-auto rounded-xl bg-black/40 p-3 text-xs text-slate-300">{finding.affected_code}</pre>}<p className="mt-3 text-sm text-cyan">Fix direction: {finding.recommendation}</p></div>)}
              </div>
            </div>
          </>}
        </div>
      </div>
    </div>
  );
}
