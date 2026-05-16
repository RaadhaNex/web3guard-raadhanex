"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-72 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

export function ThreatIntelClient() {
  const [status, setStatus] = useState<Record<string, any> | null>(null);
  const [feed, setFeed] = useState<Record<string, any> | null>(null);
  const [projectType, setProjectType] = useState("Token");
  const [chain, setChain] = useState("EVM");
  const [tags, setTags] = useState("approval,owner,multisig");
  const [title, setTitle] = useState("Manual Web3 launch threat note");
  const [summary, setSummary] = useState("A manually curated security note from RAADHANEX team. This is not a fake live news item.");
  const [category, setCategory] = useState("admin_opsec");
  const [severity, setSeverity] = useState("medium");
  const [created, setCreated] = useState<Record<string, any> | null>(null);
  const [realOnly, setRealOnly] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      const tagQuery = encodeURIComponent(tags);
      const [s, f] = await Promise.all([
        apiGet<Record<string, any>>("/threat-intel/status"),
        apiGet<Record<string, any>>(`/threat-intel/feed?project_type=${encodeURIComponent(projectType)}&chain=${encodeURIComponent(chain)}&tags=${tagQuery}&limit=20`),
      ]);
      setStatus(s); setFeed(f);
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load threat intel"); }
  }

  useEffect(() => { refresh(); }, []);

  async function createEntry() {
    setError(null);
    try {
      const row = await apiPost<Record<string, any>>("/threat-intel/admin/entries", {
        title,
        protocol_name: null,
        chain,
        category,
        severity,
        summary,
        technical_notes: "Manual/admin curated MVP entry. Add a real source URL when available.",
        affected_project_types: [projectType],
        relevance_tags: tags.split(",").map((x) => x.trim()).filter(Boolean),
        source_label: "Manual RAADHANEX entry",
        curated_by: "RAADHANEX Admin",
        real_only_acknowledged: realOnly,
      });
      setCreated(row); await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Create threat entry failed"); }
  }

  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
    <div className="max-w-4xl">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Web3Guard AI</p>
      <h1 className="mt-3 text-3xl font-black sm:text-5xl">Threat Intelligence Feed</h1>
      <p className="mt-4 text-slate-400">MVP threat intel is manual-curated + local knowledge base. It does not claim live/current news unless real feed integrations are enabled and cited.</p>
    </div>
    <div className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="space-y-5">
        <div className="card space-y-4 p-6">
          <p className="font-black text-white">Filter feed</p>
          <label className="block text-sm font-bold text-slate-200">Project type<input className="input mt-2" value={projectType} onChange={(e) => setProjectType(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Chain<input className="input mt-2" value={chain} onChange={(e) => setChain(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Tags comma separated<input className="input mt-2" value={tags} onChange={(e) => setTags(e.target.value)} /></label>
          <button className="btn-primary w-full" onClick={refresh}>Refresh Real/Manual Feed</button>
        </div>
        <div className="card space-y-4 p-6">
          <p className="font-black text-white">Add manual curated entry</p>
          <label className="block text-sm font-bold text-slate-200">Title<input className="input mt-2" value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Category<select className="input mt-2" value={category} onChange={(e) => setCategory(e.target.value)}><option value="admin_opsec">Admin OpSec</option><option value="wallet_drainer">Wallet Drainer</option><option value="reentrancy">Reentrancy</option><option value="access_control">Access Control</option><option value="oracle">Oracle</option><option value="frontend">Frontend</option><option value="api">API</option><option value="other">Other</option></select></label>
          <label className="block text-sm font-bold text-slate-200">Severity<select className="input mt-2" value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option><option value="info">Info</option></select></label>
          <textarea className="input min-h-28" value={summary} onChange={(e) => setSummary(e.target.value)} />
          <label className="flex gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50"><input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} /><span>This entry is manually curated or has real source evidence; do not present it as live news unless sourced.</span></label>
          <button className="btn-secondary w-full" onClick={createEntry}>Save Manual Threat Note</button>
        </div>
        {error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
      </div>
      <div className="space-y-5">
        <div className="card p-6"><p className="font-black text-white">Feed items</p><div className="mt-4 space-y-4">{feed?.items?.length ? feed.items.map((item: any) => <article key={item.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><SeverityBadge severity={item.severity || "info"} /><p className="mt-2 font-bold text-white">{item.title}</p><p className="mt-2 text-sm text-slate-400">{item.summary}</p><p className="mt-3 text-xs text-cyan-100">Mode: {item.status || "manual/local"} · Source: {item.source_label || "Not cited"}</p></article>) : <p className="text-sm text-slate-400">No items for this filter.</p>}</div></div>
        <div className="card p-6"><p className="font-black text-white">Threat intel status</p><div className="mt-4"><JsonBlock value={status} /></div></div>
        {created && <div className="card p-6"><p className="font-black text-white">Created manual entry</p><div className="mt-4"><JsonBlock value={created} /></div></div>}
      </div>
    </div>
  </div>;
}
