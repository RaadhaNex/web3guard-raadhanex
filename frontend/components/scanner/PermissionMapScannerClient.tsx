"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

type PermissionStatus = {
  engine_version?: string;
  live_capabilities?: string[];
  not_claimed?: string[];
};

type Capability = {
  key: string;
  label: string;
  status: string;
  controller_hint?: string;
  risk_level?: string;
  recommendation?: string;
  evidence?: Array<{ type?: string; line?: number; function?: string | null; snippet?: string }>;
};

const sampleSource = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract LaunchToken is ERC20, Ownable, Pausable {
    address public treasury;
    uint256 public feeBps;
    mapping(address => bool) public blacklisted;

    constructor(address _treasury) ERC20("Launch", "LCH") {
        treasury = _treasury;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    function pause() external onlyOwner { _pause(); }
    function unpause() external onlyOwner { _unpause(); }
    function setFee(uint256 newFeeBps) external onlyOwner { feeBps = newFeeBps; }
    function setBlacklist(address user, bool blocked) external onlyOwner { blacklisted[user] = blocked; }
    function withdraw() external onlyOwner { payable(treasury).transfer(address(this).balance); }
}`;

const sampleAbi = JSON.stringify([
  { type: "function", name: "owner", inputs: [], outputs: [{ type: "address" }] },
  { type: "function", name: "mint", inputs: [{ type: "address" }, { type: "uint256" }] },
  { type: "function", name: "pause", inputs: [] },
  { type: "function", name: "setFee", inputs: [{ type: "uint256" }] },
  { type: "function", name: "withdraw", inputs: [] },
], null, 2);

function metadata(result: ScanResponse | null, key: string): unknown {
  return result?.scan_metadata?.[key] ?? null;
}

export function PermissionMapScannerClient() {
  const [status, setStatus] = useState<PermissionStatus | null>(null);
  const [projectName, setProjectName] = useState("Permission Map Project");
  const [contractAddress, setContractAddress] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [ownerAddress, setOwnerAddress] = useState("");
  const [treasuryAddress, setTreasuryAddress] = useState("");
  const [multisigEnabled, setMultisigEnabled] = useState<"unknown" | "yes" | "no">("unknown");
  const [timelockEnabled, setTimelockEnabled] = useState<"unknown" | "yes" | "no">("unknown");
  const [solidityCode, setSolidityCode] = useState(sampleSource);
  const [abiJson, setAbiJson] = useState(sampleAbi);
  const [governanceNotes, setGovernanceNotes] = useState("Owner is planned to be moved to multisig before launch. Timelock not configured yet.");
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    apiGet<PermissionStatus>("/scan/permission-map/status").then(setStatus).catch(() => setStatus(null));
  }, []);

  const permissionMap = metadata(result, "permission_map") as { capabilities?: Capability[] } | null;
  const centralization = metadata(result, "centralization_report") as Record<string, unknown> | null;
  const transparency = metadata(result, "founder_transparency_report") as { required_disclosures?: string[]; positive_notes?: string[]; manual_review_note?: string } | null;
  const capabilities = useMemo(() => permissionMap?.capabilities || [], [permissionMap]);

  async function runScan() {
    setLoading(true);
    setError(null);
    setSaveMessage(null);
    setResult(null);
    try {
      const data = await apiPost<ScanResponse>("/scan/permission-map", {
        project_name: projectName,
        solidity_code: solidityCode.trim() || null,
        abi_json: abiJson.trim() || null,
        contract_address: contractAddress.trim() || null,
        chain,
        owner_address: ownerAddress.trim() || null,
        treasury_address: treasuryAddress.trim() || null,
        multisig_enabled: multisigEnabled === "unknown" ? null : multisigEnabled === "yes",
        timelock_enabled: timelockEnabled === "unknown" ? null : timelockEnabled === "yes",
        governance_notes: governanceNotes.trim() || null,
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Permission map scan failed");
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
        name: projectName || "Permission Map Project",
        contract_address: contractAddress || null,
        chain,
        project_type: "Permission Map + Centralization Report",
        description: "Created from permission map scanner. Role holders are not invented; unknowns remain unknown.",
      }, { headers });
      await apiPost("/scan-history", {
        user_id: userId,
        project_id: project.project.id,
        module: "permission_map",
        project_name: projectName,
        score: result.module_score.score,
        risk_label: result.module_score.risk_label,
        report_id: result.report_id,
        input_hash: result.input_hash,
        findings_count: result.findings.length,
        critical_high_count: result.findings.filter((finding) => finding.severity === "critical" || finding.severity === "high").length,
        status: "saved_from_permission_map_scanner",
        payload: result,
      }, { headers });
      setSaveMessage("Permission map saved to dashboard as a real scan record.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save permission map");
    } finally {
      setSaveLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">• Permission map</p>
        <h1 className="mt-3 text-3xl font-black sm:text-5xl">Contract Permission Map + Centralization Report</h1>
        <p className="mt-4 text-slate-400">
          Map owner, minter, pauser, upgrader, treasury, blacklist/freeze, fee, role-admin, and oracle powers from real Solidity/ABI/manual facts. Unknown role holders stay unknown; no fake governance score or private-key collection.
        </p>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-5">
          <div className="card p-6">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">
              Engine: <span className="text-cyan">{status?.engine_version || "permission-map-v1"}</span>
            </div>
            <label className="mt-4 block text-sm font-bold text-slate-200">Project name
              <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
            </label>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-bold text-slate-200">Contract address optional
                <input className="input mt-2" value={contractAddress} onChange={(event) => setContractAddress(event.target.value)} placeholder="0x..." />
              </label>
              <label className="block text-sm font-bold text-slate-200">Chain
                <input className="input mt-2" value={chain} onChange={(event) => setChain(event.target.value)} />
              </label>
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-bold text-slate-200">Owner/admin address optional
                <input className="input mt-2" value={ownerAddress} onChange={(event) => setOwnerAddress(event.target.value)} placeholder="0x... or multisig label" />
              </label>
              <label className="block text-sm font-bold text-slate-200">Treasury address optional
                <input className="input mt-2" value={treasuryAddress} onChange={(event) => setTreasuryAddress(event.target.value)} placeholder="0x..." />
              </label>
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-bold text-slate-200">Multisig evidence
                <select className="input mt-2" value={multisigEnabled} onChange={(event) => setMultisigEnabled(event.target.value as "unknown" | "yes" | "no")}>
                  <option value="unknown">Unknown / not provided</option>
                  <option value="yes">Yes, multisig planned/verified</option>
                  <option value="no">No multisig</option>
                </select>
              </label>
              <label className="block text-sm font-bold text-slate-200">Timelock evidence
                <select className="input mt-2" value={timelockEnabled} onChange={(event) => setTimelockEnabled(event.target.value as "unknown" | "yes" | "no")}>
                  <option value="unknown">Unknown / not provided</option>
                  <option value="yes">Yes, timelock planned/verified</option>
                  <option value="no">No timelock</option>
                </select>
              </label>
            </div>
            <label className="mt-4 block text-sm font-bold text-slate-200">Governance / signer notes
              <textarea className="input mt-2 min-h-28" value={governanceNotes} onChange={(event) => setGovernanceNotes(event.target.value)} />
            </label>
          </div>

          <div className="card p-6">
            <label className="block text-sm font-bold text-slate-200">Solidity source optional
              <textarea className="mono mt-2 min-h-72 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-200 outline-none focus:border-cyan/60" value={solidityCode} onChange={(event) => setSolidityCode(event.target.value)} />
            </label>
            <label className="mt-4 block text-sm font-bold text-slate-200">ABI JSON optional
              <textarea className="mono mt-2 min-h-48 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-200 outline-none focus:border-cyan/60" value={abiJson} onChange={(event) => setAbiJson(event.target.value)} />
            </label>
            <div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
              <label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} /><span>I own this project or have authorization to review these permissions.</span></label>
              <label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} /><span>I understand Web3Guard AI will not invent role holders or claim governance is safe without evidence.</span></label>
            </div>
            <button className="btn-primary mt-5 w-full" onClick={runScan} disabled={loading || !authorized || !realOnly}>{loading ? "Building permission map..." : "Build Permission Map"}</button>
            {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
          </div>
        </div>

        <div className="space-y-5">
          {!result && <div className="card p-6"><p className="font-black text-white">Real-only behavior</p><p className="mt-3 text-sm text-slate-400">Provide Solidity source, ABI JSON, or manual owner/treasury facts. If a controller cannot be verified from input, it remains unknown. No private key, seed phrase, or transaction signing is requested.</p>{status?.live_capabilities && <ul className="mt-4 space-y-2 text-sm text-slate-400">{status.live_capabilities.map((item) => <li key={item}>• {item}</li>)}</ul>}</div>}
          {result && <>
            <ScoreCard label={result.module_score.risk_label} score={result.module_score.score} />
            <div className="card p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div><p className="text-sm text-slate-400">Report</p><p className="mt-1 font-bold text-white">{result.report_id}</p><p className="mt-1 text-sm text-slate-500">{String(metadata(result, "real_only_note") || "Real input only")}</p></div>
                <button type="button" className="btn-secondary" onClick={saveToDashboard} disabled={saveLoading}>{saveLoading ? "Saving..." : "Save to Dashboard"}</button>
              </div>
              {saveMessage && <p className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">{saveMessage}</p>}
            </div>
            {centralization && <div className="grid gap-4 sm:grid-cols-2"><div className="card p-5"><p className="text-sm text-slate-400">Centralization score</p><p className="mt-2 text-4xl font-black text-white">{String(centralization.centralization_score)}</p><p className="mt-2 text-sm text-slate-400">{String(centralization.centralization_label)}</p></div><div className="card p-5"><p className="text-sm text-slate-400">Evidence</p><p className="mt-2 text-sm text-slate-300">Capabilities: {String(centralization.capability_count)}</p><p className="mt-1 text-sm text-slate-300">Multisig evidence: {String(centralization.multisig_evidence)}</p><p className="mt-1 text-sm text-slate-300">Timelock evidence: {String(centralization.timelock_evidence)}</p></div></div>}
            <div className="card p-6"><p className="text-lg font-black text-white">Permission map</p><div className="mt-4 grid gap-3">{capabilities.length === 0 && <p className="text-sm text-slate-400">No common privileged capability detected from provided evidence.</p>}{capabilities.map((capability) => <div key={capability.key} className="rounded-2xl border border-white/10 bg-black/20 p-4"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-cyan/30 bg-cyan/10 px-2.5 py-1 text-xs font-bold text-cyan">{capability.label}</span><span className="rounded-full border border-white/10 px-2.5 py-1 text-xs text-slate-300">{capability.status}</span><span className="rounded-full border border-white/10 px-2.5 py-1 text-xs text-slate-300">risk: {capability.risk_level}</span></div><p className="mt-3 text-sm text-slate-300">Controller: {capability.controller_hint || "unknown"}</p><p className="mt-2 text-sm text-cyan">Recommendation: {capability.recommendation}</p>{capability.evidence?.slice(0, 3).map((evidence, index) => <pre key={`${capability.key}-${index}`} className="mono mt-3 overflow-x-auto rounded-xl bg-black/40 p-3 text-xs text-slate-300">{evidence.line ? `line ${evidence.line}: ` : ""}{evidence.function ? `${evidence.function}(): ` : ""}{evidence.snippet}</pre>)}</div>)}</div></div>
            {transparency && <div className="card p-6"><p className="text-lg font-black text-white">Founder transparency checklist</p><div className="mt-4 space-y-2">{(transparency.required_disclosures || []).map((item) => <p key={item} className="rounded-2xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm text-amber-50">Required disclosure: {item}</p>)}{(transparency.positive_notes || []).slice(0, 5).map((item) => <p key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">{item}</p>)}</div><p className="mt-4 text-xs text-slate-500">{transparency.manual_review_note}</p></div>}
            <div className="card p-6"><p className="text-lg font-black text-white">Findings</p><div className="mt-4 space-y-3">{result.findings.map((finding) => <div key={finding.id} className="rounded-2xl border border-white/10 bg-black/20 p-4"><div className="flex flex-wrap items-center gap-2"><SeverityBadge severity={finding.severity} /><span className="text-xs text-slate-500">{finding.source}</span></div><p className="mt-3 font-bold text-white">{finding.title}</p><p className="mt-2 text-sm text-slate-400">{finding.description}</p>{finding.affected_code && <pre className="mono mt-3 overflow-x-auto rounded-xl bg-black/40 p-3 text-xs text-slate-300">{finding.affected_code}</pre>}<p className="mt-3 text-sm text-cyan">Fix direction: {finding.recommendation}</p></div>)}</div></div>
          </>}
        </div>
      </div>
    </div>
  );
}
