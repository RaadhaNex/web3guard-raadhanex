"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";

type Status = {
  ok: boolean;
  version: string;
  purpose: string;
  safe_status_labels: string[];
  supported_pattern_families: string[];
  blocked_claims: string[];
  required_disclaimer: string;
  not_supported: string[];
};

type Rule = {
  id: string;
  title: string;
  family: string;
  severity: string;
  confidence: string;
  cwe_ids: string[];
  why_it_matters: string;
  future_risk: string;
  fix: string;
  verify: string[];
};

type RuleCatalog = {
  ok: boolean;
  version: string;
  rules: Rule[];
  pattern_modules: string[];
  safe_wording: string;
};

type FormState = {
  project_name: string;
  contract_source: string;
  imports: string;
  notes: string;
  real_only_acknowledged: boolean;
};

const sampleSource = `pragma solidity ^0.8.20;

contract CustomVaultToken {
  mapping(address => uint256) public balanceOf;

  function mint(address to, uint256 amount) external {
    balanceOf[to] += amount;
  }

  function withdraw(uint256 amount) external {
    (bool ok,) = msg.sender.call{value: amount}("");
    require(ok, "transfer failed");
    balanceOf[msg.sender] -= amount;
  }
}`;

const openZeppelinSample = `pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract SaferToken is ERC20, Ownable, ReentrancyGuard, Pausable {
  constructor() ERC20("SaferToken", "SAFE") Ownable(msg.sender) {}

  function mint(address to, uint256 amount) external onlyOwner whenNotPaused {
    _mint(to, amount);
  }
}`;

const defaultForm: FormState = {
  project_name: "Pilot contract",
  contract_source: sampleSource,
  imports: "",
  notes: "Pre-audit pattern check only. Do not claim OpenZeppelin certification.",
  real_only_acknowledged: true,
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/35 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

function SeverityBadge({ severity }: { severity: string }) {
  const normalized = severity.toLowerCase();
  const tone = normalized.includes("critical")
    ? "border-red-300/30 bg-red-400/10 text-red-100"
    : normalized.includes("high")
      ? "border-orange-300/30 bg-orange-400/10 text-orange-100"
      : normalized.includes("medium")
        ? "border-amber-300/30 bg-amber-400/10 text-amber-100"
        : "border-cyan/30 bg-cyan/10 text-cyan";
  return <span className={`rounded-full border px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.16em] ${tone}`}>{severity}</span>;
}

export function OpenZeppelinPatternClient() {
  const [status, setStatus] = useState<Status | null>(null);
  const [catalog, setCatalog] = useState<RuleCatalog | null>(null);
  const [form, setForm] = useState<FormState>(defaultForm);
  const [result, setResult] = useState<any>(null);
  const [claim, setClaim] = useState("OpenZeppelin-style pattern check for supplied contracts. Not an official OpenZeppelin audit.");
  const [claimResult, setClaimResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [statusData, ruleData] = await Promise.all([
          apiGet<Status>("/openzeppelin-pattern/status"),
          apiGet<RuleCatalog>("/openzeppelin-pattern/rules"),
        ]);
        setStatus(statusData);
        setCatalog(ruleData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load OpenZeppelin pattern intelligence");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const payload = useMemo(() => ({
    project_name: form.project_name,
    contract_source: form.contract_source,
    imports: form.imports.split("\n").map((item) => item.trim()).filter(Boolean),
    notes: form.notes,
    real_only_acknowledged: form.real_only_acknowledged,
  }), [form]);

  async function analyze() {
    setError(null);
    try {
      setResult(await apiPost("/openzeppelin-pattern/analyze", payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "OpenZeppelin pattern analysis failed");
    }
  }

  async function checkClaim() {
    setError(null);
    try {
      setClaimResult(await apiPost("/openzeppelin-pattern/claim-check", { text: claim, real_only_acknowledged: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    }
  }

  if (loading) return <CommandLoadingState label="Loading OpenZeppelin pattern intelligence..." />;

  return (
    <section className="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-6">
        {error ? <CommandNotice tone="danger" title="OpenZeppelin pattern error" text={error} /> : null}

        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Pattern setup</p>
              <h2 className="mt-2 text-2xl font-black text-white">Paste Solidity source or imports</h2>
            </div>
            <StatusPill status={status?.ok ? "Pattern engine live" : "Not assessed yet"} />
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-400">{status?.required_disclaimer}</p>
          <div className="mt-5 grid gap-3">
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Project name<input className="form-input" value={form.project_name} onChange={(e) => setForm({ ...form, project_name: e.target.value })} /></label>
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Imports, one per line<textarea className="form-input min-h-24" value={form.imports} onChange={(e) => setForm({ ...form, imports: e.target.value })} placeholder='import "@openzeppelin/contracts/token/ERC20/ERC20.sol";' /></label>
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Solidity/source evidence<textarea className="form-input min-h-[340px] font-mono text-xs" value={form.contract_source} onChange={(e) => setForm({ ...form, contract_source: e.target.value })} /></label>
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Notes<textarea className="form-input min-h-20" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
            <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300"><input type="checkbox" checked={form.real_only_acknowledged} onChange={(e) => setForm({ ...form, real_only_acknowledged: e.target.checked })} /> I understand this is pattern intelligence only, not official OpenZeppelin certification or a certified audit.</label>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="btn-primary" onClick={analyze}>Analyze patterns</button>
            <button className="btn-secondary" onClick={() => setForm({ ...form, contract_source: sampleSource, imports: "" })}>Load risky sample</button>
            <button className="btn-secondary" onClick={() => setForm({ ...form, contract_source: openZeppelinSample, imports: "" })}>Load OZ-style sample</button>
          </div>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Claim safety</p>
          <h2 className="mt-2 text-2xl font-black text-white">Block fake OpenZeppelin claims</h2>
          <textarea className="form-input mt-4 min-h-24" value={claim} onChange={(e) => setClaim(e.target.value)} />
          <button className="btn-secondary mt-3" onClick={checkClaim}>Check wording</button>
          {claimResult ? <div className="mt-4"><JsonBlock value={claimResult} /></div> : null}
        </article>
      </div>

      <div className="space-y-6">
        <article className="clean-panel p-6">
          <p className="section-label">Supported secure pattern families</p>
          <h2 className="mt-2 text-2xl font-black text-white">OpenZeppelin-style modules</h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {catalog?.pattern_modules.map((item) => <span key={item} className="rounded-full border border-cyan/20 bg-cyan/10 px-3 py-1 text-xs font-bold text-cyan">{item}</span>)}
          </div>
          <h3 className="mt-6 text-sm font-black uppercase tracking-[0.18em] text-red-200">Blocked wording</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {status?.blocked_claims.map((item) => <span key={item} className="rounded-full border border-red-500/20 bg-red-500/10 px-3 py-1 text-xs font-bold text-red-100">{item}</span>)}
          </div>
        </article>

        {result ? (
          <article className="clean-panel p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="section-label">Pattern result</p>
                <h2 className="mt-2 text-2xl font-black text-white">{result.findings_count ?? 0} findings / advisories</h2>
              </div>
              <StatusPill status={result.pattern_summary?.uses_openzeppelin_contracts ? "OZ pattern detected" : "Custom implementation detected"} />
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {Object.entries(result.pattern_summary || {}).map(([key, value]) => (
                <div key={key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-[11px] font-black uppercase tracking-[0.16em] text-slate-500">{key.replaceAll("_", " ")}</p>
                  <p className="mt-2 text-sm font-bold text-white">{String(value)}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 space-y-3">
              {result.findings?.map((finding: any) => (
                <div key={finding.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <SeverityBadge severity={finding.severity} />
                    <StatusPill status={finding.status} />
                    <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.16em] text-slate-300">{finding.priority}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-black text-white">{finding.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{finding.impact}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300"><span className="font-bold text-white">Future risk:</span> {finding.future_risk}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300"><span className="font-bold text-white">Fix:</span> {finding.fix_plan?.summary}</p>
                </div>
              ))}
            </div>
          </article>
        ) : (
          <article className="clean-panel p-6">
            <p className="section-label">Result</p>
            <p className="mt-3 text-sm leading-6 text-slate-400">Run analysis to see detected OpenZeppelin modules, pattern gaps, impact, future risk, and fix verification guidance.</p>
          </article>
        )}

        <article className="clean-panel p-6">
          <p className="section-label">Raw evidence output</p>
          {result ? <JsonBlock value={result} /> : <p className="mt-3 text-sm text-slate-400">No output yet.</p>}
        </article>
      </div>
    </section>
  );
}
