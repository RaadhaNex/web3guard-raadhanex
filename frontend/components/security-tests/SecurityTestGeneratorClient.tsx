"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type StatusResponse = {
  ok: boolean;
  phase: string;
  capabilities: string[];
  frameworks: string[];
  blocked_capabilities: string[];
  real_only_note: string;
  safe_boundary: string;
};

type TemplateItem = {
  id: string;
  framework: string;
  filename: string;
  title: string;
  description: string;
  language: string;
  content: string;
  commands: string[];
  review_note: string;
  extra_files?: Array<{ filename: string; content: string }>;
};

type TestPack = {
  ok: boolean;
  generated_at: string;
  bundle_id: string;
  contract_name: string;
  project_type: string;
  risk_focus: string[];
  frameworks: string[];
  templates: TemplateItem[];
  commands: Array<{ label: string; command: string; requires: string; safe_boundary: string }>;
  blocked_use_cases: string[];
  real_only_note: string;
  safe_boundary: string;
};

const frameworkOptions = [
  ["foundry", "Foundry tests"],
  ["echidna", "Echidna properties"],
  ["slither", "Slither commands"],
  ["aderyn", "Aderyn commands"],
  ["semgrep", "Semgrep rules"],
];

const defaultRisks = "reentrancy, access control, owner abuse, upgrade authorization, allowance UX";

function splitRisks(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 20);
}

function CodeBlock({ title, filename, code }: { title: string; filename: string; code: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/35">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-white/[0.03] px-4 py-3">
        <div>
          <p className="text-sm font-black text-white">{title}</p>
          <p className="mono mt-1 text-xs text-slate-500">{filename}</p>
        </div>
        <button type="button" className="btn-secondary !px-3 !py-2 text-xs" onClick={copy}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="max-h-[420px] overflow-auto p-4 text-xs leading-6 text-slate-200"><code>{code}</code></pre>
    </div>
  );
}

export function SecurityTestGeneratorClient() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [pack, setPack] = useState<TestPack | null>(null);
  const [contractName, setContractName] = useState("TargetContract");
  const [projectType, setProjectType] = useState("Web3 launch");
  const [risks, setRisks] = useState(defaultRisks);
  const [frameworks, setFrameworks] = useState<string[]>(["foundry", "echidna", "slither", "aderyn", "semgrep"]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<StatusResponse>("/security-tests/status");
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Security test generator status failed.");
    } finally {
      setLoading(false);
    }
  }

  async function generate() {
    setGenerating(true);
    setError(null);
    try {
      const data = await apiPost<TestPack>("/security-tests/generate", {
        contract_name: contractName,
        project_type: projectType,
        risk_focus: splitRisks(risks),
        frameworks,
      });
      setPack(data);
      setSelectedTemplate(data.templates[0]?.id || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate defensive test pack.");
    } finally {
      setGenerating(false);
    }
  }

  function toggleFramework(key: string) {
    setFrameworks((current) => {
      if (current.includes(key)) return current.filter((item) => item !== key);
      return [...current, key];
    });
  }

  useEffect(() => {
    void loadStatus();
  }, []);

  const activeTemplate = useMemo(() => pack?.templates.find((item) => item.id === selectedTemplate) || pack?.templates[0], [pack, selectedTemplate]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="section-label">Phase 17 · Security Test Generator</p>
          <h1 className="mt-3 max-w-5xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
            Generate defensive local test packs before asking for manual review.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
            Create Foundry tests, Echidna property harnesses, Slither/Aderyn command packs, and Semgrep rules as starter material. Web3Guard does not run these tools here and does not claim generated templates are an audit.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/eon" className="btn-secondary">EON Risk Graph</Link>
          <Link href="/engine-depth" className="btn-secondary">Engine Depth</Link>
        </div>
      </div>

      {loading ? <CommandLoadingState label="Loading security test generator status..." /> : null}
      {error ? <CommandNotice tone="danger" title="Generator issue" text={error} /> : null}

      {status ? (
        <section className="mb-8 grid gap-4 lg:grid-cols-3">
          <div className="command-card p-5 lg:col-span-2">
            <h2 className="text-xl font-black text-white">Defensive scope</h2>
            <p className="mt-3 text-sm leading-7 text-slate-400">{status.real_only_note}</p>
            <p className="mt-3 text-sm leading-7 text-slate-400">{status.safe_boundary}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {status.capabilities.map((item) => <span key={item} className="badge badge-cyan">{item}</span>)}
            </div>
          </div>
          <div className="command-card p-5">
            <h2 className="text-xl font-black text-white">Blocked uses</h2>
            <div className="mt-4 grid gap-2">
              {status.blocked_capabilities.map((item) => <span key={item} className="badge badge-red">{item}</span>)}
            </div>
          </div>
        </section>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="command-card p-5">
          <h2 className="text-2xl font-black text-white">Build a local test pack</h2>
          <div className="mt-5 grid gap-4">
            <label className="grid gap-2 text-sm font-bold text-slate-300">
              Contract or project name
              <input className="input" value={contractName} onChange={(event) => setContractName(event.target.value)} placeholder="VaultToken" />
            </label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">
              Project type
              <input className="input" value={projectType} onChange={(event) => setProjectType(event.target.value)} placeholder="ERC20 launch, DAO, marketplace, DeFi vault" />
            </label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">
              Risk focus, comma separated
              <textarea className="textarea min-h-[130px]" value={risks} onChange={(event) => setRisks(event.target.value)} />
            </label>
            <div>
              <p className="text-sm font-bold text-slate-300">Frameworks</p>
              <div className="mt-3 grid gap-2">
                {frameworkOptions.map(([key, label]) => (
                  <label key={key} className="flex cursor-pointer items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
                    <span>{label}</span>
                    <input type="checkbox" checked={frameworks.includes(key)} onChange={() => toggleFramework(key)} />
                  </label>
                ))}
              </div>
            </div>
            <button type="button" className="btn-primary" disabled={generating || frameworks.length === 0} onClick={() => void generate()}>
              {generating ? "Generating..." : "Generate defensive test pack"}
            </button>
          </div>
        </div>

        <div className="grid gap-5">
          {pack ? (
            <>
              <div className="command-card p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="mono text-xs font-bold uppercase tracking-[0.2em] text-cyan">{pack.bundle_id}</p>
                    <h2 className="mt-2 text-2xl font-black text-white">Generated local test pack</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{pack.safe_boundary}</p>
                  </div>
                  <span className="badge badge-green">Starter templates only</span>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <div className="stat-slab p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Templates</p><p className="mt-2 text-2xl font-black text-white">{pack.templates.length}</p></div>
                  <div className="stat-slab p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Frameworks</p><p className="mt-2 text-2xl font-black text-white">{pack.frameworks.length}</p></div>
                  <div className="stat-slab p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Risks</p><p className="mt-2 text-2xl font-black text-white">{pack.risk_focus.length}</p></div>
                </div>
              </div>

              <div className="command-card p-5">
                <h3 className="text-xl font-black text-white">Templates</h3>
                <div className="mt-4 flex flex-wrap gap-2">
                  {pack.templates.map((template) => (
                    <button
                      type="button"
                      key={template.id}
                      className={`rounded-full border px-3 py-1 text-xs font-black ${activeTemplate?.id === template.id ? "border-cyan/40 bg-cyan/10 text-cyan" : "border-white/10 bg-white/[0.03] text-slate-400"}`}
                      onClick={() => setSelectedTemplate(template.id)}
                    >
                      {template.framework}
                    </button>
                  ))}
                </div>
                {activeTemplate ? (
                  <div className="mt-5 grid gap-4">
                    <CommandNotice tone="warning" title={activeTemplate.title} text={activeTemplate.review_note} />
                    <CodeBlock title={activeTemplate.title} filename={activeTemplate.filename} code={activeTemplate.content} />
                    {activeTemplate.extra_files?.map((file) => (
                      <CodeBlock key={file.filename} title="Extra file" filename={file.filename} code={file.content} />
                    ))}
                  </div>
                ) : null}
              </div>

              <div className="grid gap-5 lg:grid-cols-2">
                <div className="command-card p-5">
                  <h3 className="text-xl font-black text-white">Local commands</h3>
                  <div className="mt-4 grid gap-3">
                    {pack.commands.map((command) => (
                      <div key={command.label} className="rounded-2xl border border-white/10 bg-black/25 p-4">
                        <p className="font-black text-white">{command.label}</p>
                        <p className="mono mt-2 break-all text-xs text-cyan">{command.command}</p>
                        <p className="mt-2 text-xs leading-5 text-slate-400">Requires: {command.requires}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="command-card p-5">
                  <h3 className="text-xl font-black text-white">Blocked use cases</h3>
                  <div className="mt-4 grid gap-2">
                    {pack.blocked_use_cases.map((item) => <span key={item} className="badge badge-red">{item}</span>)}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <CommandEmptyState title="No test pack generated yet" text="Enter a contract/project name and choose frameworks. The generated output is starter material for local defensive testing only." />
          )}
        </div>
      </section>
    </main>
  );
}
