"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

const oldCode = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract TokenV1 {
  address public owner;
  modifier onlyOwner(){ require(msg.sender == owner, "owner"); _; }
  constructor(){ owner = msg.sender; }
}`;
const newCode = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract TokenV2 {
  address public owner;
  uint256 public feeBps;
  mapping(address => bool) public blacklisted;
  modifier onlyOwner(){ require(msg.sender == owner, "owner"); _; }
  constructor(){ owner = msg.sender; }
  function mint(address to, uint256 amount) external onlyOwner {}
  function setFee(uint256 fee) external onlyOwner { feeBps = fee; }
  function setBlacklist(address user, bool blocked) external onlyOwner { blacklisted[user] = blocked; }
  function upgradeTo(address implementation) external onlyOwner {}
}`;

export function ContractDiffScannerClient() {
  const [projectName, setProjectName] = useState("Contract Diff Project");
  const [oldSource, setOldSource] = useState(oldCode);
  const [newSource, setNewSource] = useState(newCode);
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function runScan() { setLoading(true); setError(null); setResult(null); try { const data = await apiPost<ScanResponse>("/scan/contract-diff", { project_name: projectName, old_code: oldSource, new_code: newSource, contract_type: "general", authorization_confirmed: authorized, real_only_acknowledged: realOnly }); setResult(data); } catch (err) { setError(err instanceof Error ? err.message : "Diff scan failed"); } finally { setLoading(false); } }
  const meta = result?.scan_metadata || {};
  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8"><div className="max-w-4xl"><p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Web3Guard AI</p><h1 className="mt-3 text-3xl font-black sm:text-5xl">Contract Diff + Audit History</h1><p className="mt-4 text-slate-400">Compare old vs new Solidity source, identify newly introduced risky patterns, and summarize fixed/open/new finding keys. No auto-fix and no fake semantic proof.</p></div><div className="mt-8 grid gap-6 lg:grid-cols-2"><div className="space-y-5"><div className="card p-6"><label className="block text-sm font-bold text-slate-200">Project name<input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} /></label><label className="mt-4 block text-sm font-bold text-slate-200">Old Solidity source<textarea className="mono mt-2 min-h-72 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-200 outline-none focus:border-cyan/60" value={oldSource} onChange={(e) => setOldSource(e.target.value)} /></label><label className="mt-4 block text-sm font-bold text-slate-200">New Solidity source<textarea className="mono mt-2 min-h-72 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-200 outline-none focus:border-cyan/60" value={newSource} onChange={(e) => setNewSource(e.target.value)} /></label><div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50"><label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /><span>I own this project or have authorization to compare these versions.</span></label><label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} /><span>I understand this does not auto-apply fixes or prove upgrade safety.</span></label></div><button className="btn-primary mt-5 w-full" onClick={runScan} disabled={loading || !authorized || !realOnly}>{loading ? "Comparing..." : "Compare Contracts"}</button>{error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}</div></div><div className="space-y-5">{!result && <div className="card p-6"><p className="font-black text-white">Real diff mode</p><p className="mt-3 text-sm text-slate-400">Both old and new source are required. Identical source is rejected. Added risks are found from actual added lines and rule-engine deltas.</p></div>}{result && <><ScoreCard label={result.module_score.risk_label} score={result.module_score.score} /><div className="grid gap-4 sm:grid-cols-3"><div className="card p-4"><p className="text-xs text-slate-500">Old score</p><p className="text-2xl font-black text-white">{String(meta.old_score ?? "-")}</p></div><div className="card p-4"><p className="text-xs text-slate-500">New score</p><p className="text-2xl font-black text-white">{String(meta.new_score ?? "-")}</p></div><div className="card p-4"><p className="text-xs text-slate-500">Delta</p><p className="text-2xl font-black text-white">{String(meta.score_delta ?? "-")}</p></div></div><div className="card p-6"><p className="font-black text-white">Diff summary</p><p className="mt-3 text-sm text-slate-400">Added lines: {String(meta.added_line_count ?? 0)} • Removed lines: {String(meta.removed_line_count ?? 0)}</p><pre className="mono mt-4 max-h-96 overflow-auto rounded-2xl bg-black/40 p-4 text-xs text-slate-300">{String(meta.diff_preview || "")}</pre></div><div className="card p-6"><p className="font-black text-white">Findings</p><div className="mt-4 space-y-4">{result.findings.map((finding) => <div key={finding.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><SeverityBadge severity={finding.severity} /><p className="mt-2 font-bold text-white">{finding.title}</p><p className="mt-2 text-sm text-slate-400">{finding.recommendation}</p>{finding.affected_code && <pre className="mono mt-3 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-slate-300">{finding.affected_code}</pre>}</div>)}</div></div></>}</div></div></div>;
}
