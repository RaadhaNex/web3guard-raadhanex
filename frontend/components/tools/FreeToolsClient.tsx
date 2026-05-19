"use client";

import { useMemo, useState } from "react";
import { freeTools } from "@/lib/publicBetaContent";

function toolTone(index: number) {
  const tones = ["badge-cyan", "badge-green", "badge-purple", "badge-amber"];
  return tones[index % tones.length];
}

export function FreeToolsClient() {
  const [projectName, setProjectName] = useState("My Web3 Project");
  const [domain, setDomain] = useState("example.com");
  const [toolIndex, setToolIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  const current = freeTools[toolIndex] ?? freeTools[0];
  const output = useMemo(
    () => current.template(projectName.trim() || "My Web3 Project", domain.trim() || "example.com"),
    [current, domain, projectName]
  );
  const lineCount = output.split("\n").length;

  async function copy() {
    await navigator.clipboard.writeText(output);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  }

  function download() {
    const blob = new Blob([output], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${current.outputTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "web3guard-tool"}.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-8 grid gap-4 md:grid-cols-3">
        {[
          ["10", "free artifacts", "checklists, policies, CI starters"],
          ["0", "provider calls", "runs locally in your browser UI"],
          ["safe", "beta posture", "no fake integration claims"],
        ].map(([value, label, note]) => (
          <div key={label} className="stat-slab p-5">
            <p className="text-3xl font-black text-white">{value}</p>
            <p className="mt-1 text-xs font-black uppercase tracking-[0.2em] text-cyan">{label}</p>
            <p className="mt-2 text-sm text-slate-500">{note}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="tool-console p-5">
          <div className="relative z-[1]">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="section-label">Free tool console</p>
                <h2 className="mt-3 text-2xl font-black text-white">Generate launch artifacts fast.</h2>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  These generators stay honest: no payment, AI, wallet, scanner, or external-provider call is made here.
                </p>
              </div>
              <span className="badge badge-green">Local output</span>
            </div>

            <div className="mt-5 grid gap-3">
              <label className="text-sm font-bold text-slate-200">
                Project name
                <input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} />
              </label>
              <label className="text-sm font-bold text-slate-200">
                Domain
                <input className="input mt-2" value={domain} onChange={(e) => setDomain(e.target.value)} />
              </label>
            </div>

            <div className="mt-6 grid gap-2">
              {freeTools.map((tool, index) => (
                <button
                  key={tool.title}
                  type="button"
                  onClick={() => setToolIndex(index)}
                  className={`status-node p-4 text-left text-sm transition hover:-translate-y-0.5 hover:border-cyan/25 ${
                    index === toolIndex ? "border-cyan/30 bg-cyan/10" : "border-white/10 bg-black/20"
                  }`}
                >
                  <span className={`badge ${toolTone(index)}`}>0{index + 1}</span>
                  <span className="mt-3 block font-black text-white">{tool.title}</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-400">{tool.description}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="tool-console p-5 shadow-soft">
          <div className="relative z-[1]">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-emerald-300">Generated artifact</p>
                <h3 className="mt-2 text-2xl font-black text-white">{current.outputTitle}</h3>
                <p className="mt-2 text-xs text-slate-500">{lineCount} lines · text artifact · editable after download</p>
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary" type="button" onClick={copy}>{copied ? "Copied" : "Copy"}</button>
                <button className="btn-primary" type="button" onClick={download}>Download</button>
              </div>
            </div>

            <div className="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-black/55">
              <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-red-400" />
                  <span className="h-3 w-3 rounded-full bg-yellow-300" />
                  <span className="h-3 w-3 rounded-full bg-emerald-400" />
                </div>
                <p className="mono text-[11px] text-slate-500">{current.outputTitle.toLowerCase().replace(/\s+/g, "-")}.txt</p>
              </div>
              <textarea readOnly value={output} className="min-h-[560px] w-full border-0 bg-transparent p-4 font-mono text-xs leading-5 text-slate-100 outline-none" />
            </div>

            <div className="mt-4 grid gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-xs leading-5 text-amber-100 sm:grid-cols-2">
              <p><strong>Reminder:</strong> review generated text before publishing.</p>
              <p><strong>Boundary:</strong> this is guidance, not legal advice or a certified audit artifact.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
