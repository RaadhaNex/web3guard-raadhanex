"use client";

import { useMemo, useState } from "react";
import { freeTools } from "@/lib/publicBetaContent";

export function FreeToolsClient() {
  const [projectName, setProjectName] = useState("My Web3 Project");
  const [domain, setDomain] = useState("example.com");
  const [toolIndex, setToolIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  const current = freeTools[toolIndex] ?? freeTools[0];
  const output = useMemo(() => current.template(projectName.trim() || "My Web3 Project", domain.trim() || "example.com"), [current, domain, projectName]);

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
      <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <p className="section-label text-risk-yellow">Free tools</p>
          <h2 className="mt-3 text-2xl font-black text-white">Generate useful launch artifacts.</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">These tools are static/readiness generators. They do not call payment, AI, wallets, or external providers.</p>
          <div className="mt-5 grid gap-3">
            <label className="text-sm font-bold text-slate-200">Project name<input className="mt-2 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-risk-yellow" value={projectName} onChange={(e) => setProjectName(e.target.value)} /></label>
            <label className="text-sm font-bold text-slate-200">Domain<input className="mt-2 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-risk-yellow" value={domain} onChange={(e) => setDomain(e.target.value)} /></label>
          </div>
          <div className="mt-6 grid gap-2">
            {freeTools.map((tool, index) => (
              <button key={tool.title} type="button" onClick={() => setToolIndex(index)} className={`rounded-2xl border px-4 py-3 text-left text-sm transition ${index === toolIndex ? "border-risk-yellow bg-risk-yellow/10 text-yellow-100" : "border-white/10 bg-black/20 text-slate-300 hover:border-white/25"}`}>
                <span className="font-black">{tool.title}</span>
                <span className="mt-1 block text-xs leading-5 text-slate-400">{tool.description}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="rounded-3xl border border-white/10 bg-[#07101f] p-5 shadow-soft">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div><p className="text-xs font-black uppercase tracking-[0.24em] text-risk-green">Generated artifact</p><h3 className="mt-2 text-2xl font-black text-white">{current.outputTitle}</h3></div>
            <div className="flex gap-2"><button className="btn-secondary" type="button" onClick={copy}>{copied ? "Copied" : "Copy"}</button><button className="btn-primary" type="button" onClick={download}>Download</button></div>
          </div>
          <textarea readOnly value={output} className="mt-5 min-h-[560px] w-full rounded-2xl border border-white/10 bg-black/50 p-4 font-mono text-xs leading-5 text-slate-100 outline-none" />
        </div>
      </div>
    </section>
  );
}
