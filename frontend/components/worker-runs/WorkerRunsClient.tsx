"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";

type WorkerTool = {
  key: string;
  name: string;
  status: string;
  installed: boolean;
  will_run: boolean;
  command_template: string;
  next_action: string;
};

type WorkerRunStatus = {
  ok: boolean;
  version: string;
  purpose: string;
  static_execution_ready_tools: string[];
  static_analysis_enabled: boolean;
  worker_execution_enabled: boolean;
  deep_analysis_enabled: boolean;
  mythril_policy: string;
  tools: WorkerTool[];
  execution_modes: Record<string, string>;
  safety_boundaries: Record<string, boolean>;
  blocked_claims: string[];
};

type ManifestStep = {
  order: number;
  tool: string;
  name: string;
  status: string;
  will_run_now: boolean;
  installed: boolean;
  command_template: string;
  evidence_policy: string;
  timeout_policy: Record<string, string | number>;
  storage_policy: string;
  when_missing: string;
  next_action: string;
};

type ManifestResponse = {
  ok: boolean;
  version: string;
  project_name: string;
  project_type: string;
  steps: ManifestStep[];
  recommended_runtime: Record<string, string>;
  blocked_actions: string[];
};

type Finding = {
  id: string;
  tool: string;
  status: string;
  severity: string;
  title: string;
  description: string;
  source: string;
  evidence_id: string;
  limitation: string;
};

type WorkerRunResponse = {
  ok: boolean;
  version: string;
  mode?: string;
  status: string;
  input_hash?: string;
  requested_tools?: string[];
  findings: Finding[];
  real_findings_count: number;
  limitation?: string;
  evidence_mode?: string;
  tool?: string;
  evidence?: Array<Record<string, string>>;
  note?: string;
};

const SAMPLE_CONTRACT = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Phase33Sample {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function riskyWithdraw(address payable to) external {
        require(tx.origin == owner, "not owner");
        to.call{value: address(this).balance}("");
    }
}`;

const MYTHRIL_SAMPLE = JSON.stringify(
  {
    issues: [
      {
        title: "External Call To User-Supplied Address",
        severity: "High",
        "swc-id": "SWC-107",
        description: "Imported Mythril JSON sample used for parser validation only.",
      },
    ],
  },
  null,
  2,
);

function asJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function severityClass(severity: string) {
  const value = severity.toLowerCase();
  if (value.includes("critical")) return "border-red-400/30 bg-red-500/10 text-red-100";
  if (value.includes("high")) return "border-orange-400/30 bg-orange-400/10 text-orange-100";
  if (value.includes("medium")) return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  return "border-cyan/30 bg-cyan/10 text-cyan";
}

function ToolGrid({ tools }: { tools: WorkerTool[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {tools.map((tool) => (
        <article className="glass-tile p-5" key={tool.key}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-500">{tool.key}</p>
              <h3 className="mt-2 text-lg font-black text-white">{tool.name}</h3>
            </div>
            <StatusPill status={tool.status} />
          </div>
          <div className="mt-4 grid gap-2 text-xs text-slate-400">
            <p><strong className="text-white">Installed:</strong> {tool.installed ? "yes" : "no"}</p>
            <p><strong className="text-white">Will run now:</strong> {tool.will_run ? "yes" : "no"}</p>
            <p className="mono rounded-2xl border border-white/10 bg-black/30 p-3 text-[11px] leading-5 text-slate-300">{tool.command_template}</p>
          </div>
          <p className="mt-4 text-xs leading-5 text-slate-500">{tool.next_action}</p>
        </article>
      ))}
    </div>
  );
}

function FindingsList({ findings }: { findings: Finding[] }) {
  if (!findings.length) {
    return (
      <div className="empty-state">
        <h3 className="text-lg font-black text-white">No real worker findings yet</h3>
        <p className="mt-2 text-sm text-slate-400">Missing or disabled tools remain Not Assessed. Web3Guard does not invent scanner findings.</p>
      </div>
    );
  }
  return (
    <div className="grid gap-4">
      {findings.map((finding) => (
        <article className="glass-tile p-5" key={finding.id}>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`rounded-full border px-3 py-1 text-xs font-black uppercase tracking-[0.14em] ${severityClass(finding.severity)}`}>{finding.severity}</span>
            <StatusPill status={finding.status} />
            <span className="mono text-xs text-slate-500">{finding.tool}</span>
          </div>
          <h3 className="mt-4 text-xl font-black text-white">{finding.title}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-400">{finding.description}</p>
          <div className="mt-4 grid gap-2 text-xs text-slate-500 md:grid-cols-2">
            <p><strong className="text-slate-200">Source:</strong> {finding.source}</p>
            <p><strong className="text-slate-200">Evidence:</strong> {finding.evidence_id}</p>
          </div>
          <p className="mt-3 text-xs leading-5 text-slate-500">{finding.limitation}</p>
        </article>
      ))}
    </div>
  );
}

export function WorkerRunsClient() {
  const [status, setStatus] = useState<WorkerRunStatus | null>(null);
  const [manifest, setManifest] = useState<ManifestResponse | null>(null);
  const [staticResult, setStaticResult] = useState<WorkerRunResponse | null>(null);
  const [importResult, setImportResult] = useState<WorkerRunResponse | null>(null);
  const [source, setSource] = useState(SAMPLE_CONTRACT);
  const [toolJson, setToolJson] = useState(MYTHRIL_SAMPLE);
  const [importTool, setImportTool] = useState("mythril");
  const [executeStatic, setExecuteStatic] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readyCount = useMemo(() => status?.tools.filter((tool) => tool.will_run).length ?? 0, [status]);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const nextStatus = await apiGet<WorkerRunStatus>("/worker-runs/status");
        const nextManifest = await apiPost<ManifestResponse>("/worker-runs/manifest", {
          project_name: "Phase 33 worker preview",
          project_type: "Solidity static + deep worker evidence",
          tools: ["slither", "semgrep", "aderyn", "foundry", "echidna", "mythril"],
          real_only_acknowledged: true,
        });
        if (active) {
          setStatus(nextStatus);
          setManifest(nextManifest);
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Failed to load worker run status");
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  async function runStatic() {
    setBusy(true);
    setError(null);
    try {
      const response = await apiPost<WorkerRunResponse>("/worker-runs/static", {
        project_name: "Phase 33 local static worker",
        source_code: source,
        file_name: "Phase33Sample.sol",
        tools: ["slither", "semgrep", "aderyn"],
        execute: executeStatic,
        real_only_acknowledged: true,
      });
      setStaticResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Static worker request failed");
    } finally {
      setBusy(false);
    }
  }

  async function importJson() {
    setBusy(true);
    setError(null);
    try {
      const response = await apiPost<WorkerRunResponse>("/worker-runs/import-json", {
        tool: importTool,
        tool_json: toolJson,
        generated_by_web3guard_worker: false,
        real_only_acknowledged: true,
      });
      setImportResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import worker JSON failed");
    } finally {
      setBusy(false);
    }
  }

  if (!status) {
    return <div className="mt-8"><CommandLoadingState label="Loading Phase 33 worker run engine..." /></div>;
  }

  return (
    <section className="mt-8 grid gap-6">
      {error ? <CommandNotice tone="danger" title="Worker run request failed" text={error} /> : null}
      <div className="grid gap-4 lg:grid-cols-4">
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-500">Ready tools</p>
          <p className="mt-3 text-4xl font-black text-white">{readyCount}/{status.tools.length}</p>
          <p className="mt-2 text-sm text-slate-400">Only enabled and installed tools can create worker evidence.</p>
        </div>
        <div className="command-card p-5 lg:col-span-3">
          <p className="text-sm font-black text-white">Safety boundaries</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(status.safety_boundaries).map(([key, value]) => (
              <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-300" key={key}>{key.replaceAll("_", " ")}: {value ? "yes" : "no"}</span>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-400">{status.purpose}</p>
        </div>
      </div>

      <ToolGrid tools={status.tools} />

      <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <article className="command-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Static worker run</p>
              <h2 className="mt-2 text-2xl font-black text-white">Slither / Semgrep / Aderyn evidence</h2>
            </div>
            <label className="flex items-center gap-2 text-sm font-bold text-slate-300">
              <input className="h-4 w-4" type="checkbox" checked={executeStatic} onChange={(event) => setExecuteStatic(event.target.checked)} />
              Execute if installed
            </label>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-400">Unchecked mode returns a safe manifest only. Checked mode runs only configured local workers and never creates fake findings for missing tools.</p>
          <textarea className="mt-4 min-h-64 w-full rounded-3xl border border-white/10 bg-black/40 p-4 mono text-xs leading-5 text-slate-200 outline-none focus:border-cyan/40" value={source} onChange={(event) => setSource(event.target.value)} />
          <button className="btn-primary mt-4" disabled={busy} onClick={runStatic}>{busy ? "Working..." : executeStatic ? "Run configured workers" : "Create safe run plan"}</button>
        </article>

        <article className="command-card p-5">
          <p className="section-label">Import deep worker JSON</p>
          <h2 className="mt-2 text-2xl font-black text-white">Mythril / Echidna / Foundry parser</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">Use this for worker output produced outside the API. Imported evidence is labeled separately until verified by your configured worker.</p>
          <select className="mt-4 w-full rounded-2xl border border-white/10 bg-black/40 p-3 text-sm text-white outline-none" value={importTool} onChange={(event) => setImportTool(event.target.value)}>
            {[
              "mythril",
              "echidna",
              "foundry",
              "slither",
              "semgrep",
              "aderyn",
            ].map((tool) => <option key={tool} value={tool}>{tool}</option>)}
          </select>
          <textarea className="mt-4 min-h-64 w-full rounded-3xl border border-white/10 bg-black/40 p-4 mono text-xs leading-5 text-slate-200 outline-none focus:border-cyan/40" value={toolJson} onChange={(event) => setToolJson(event.target.value)} />
          <button className="btn-secondary mt-4" disabled={busy} onClick={importJson}>{busy ? "Working..." : "Normalize imported JSON"}</button>
        </article>
      </div>

      {staticResult ? (
        <article className="command-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Static worker result</p>
              <h2 className="mt-2 text-2xl font-black text-white">{staticResult.mode}</h2>
            </div>
            <StatusPill status={staticResult.status} />
          </div>
          {staticResult.note ? <CommandNotice tone="info" title="No subprocess executed" text={staticResult.note} /> : null}
          <div className="mt-5"><FindingsList findings={staticResult.findings || []} /></div>
        </article>
      ) : null}

      {importResult ? (
        <article className="command-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Imported worker JSON</p>
              <h2 className="mt-2 text-2xl font-black text-white">{importResult.tool} · {importResult.evidence_mode}</h2>
            </div>
            <StatusPill status={importResult.status} />
          </div>
          <div className="mt-5"><FindingsList findings={importResult.findings || []} /></div>
        </article>
      ) : null}

      {manifest ? (
        <article className="command-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Safe worker manifest</p>
              <h2 className="mt-2 text-2xl font-black text-white">{manifest.project_name}</h2>
            </div>
            <Link href="/results" className="btn-secondary">Open results engine</Link>
          </div>
          <div className="mt-5 grid gap-3">
            {manifest.steps.map((step) => (
              <details className="rounded-2xl border border-white/10 bg-white/[0.03] p-4" key={`${step.order}-${step.tool}`}>
                <summary className="cursor-pointer text-sm font-black text-white">{step.order}. {step.name} · {step.status}</summary>
                <pre className="mt-3 overflow-auto rounded-2xl bg-black/40 p-3 mono text-xs leading-5 text-slate-300">{asJson(step)}</pre>
              </details>
            ))}
          </div>
        </article>
      ) : null}
    </section>
  );
}
