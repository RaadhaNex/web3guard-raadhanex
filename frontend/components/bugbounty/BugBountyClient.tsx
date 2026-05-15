"use client";

import { useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Program = Record<string, any>;
type Submission = Record<string, any>;
function JsonBlock({ value }: { value: unknown }) { return <pre className="mono max-h-80 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>; }

export function BugBountyClient() {
  const [projectName, setProjectName] = useState("RAADHANEX Token Launch");
  const [scope, setScope] = useState("In scope: listed contracts, launch website, wallet flow and public APIs for safe non-destructive testing only.");
  const [email, setEmail] = useState("security@raadhanex.example");
  const [authorized, setAuthorized] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [error, setError] = useState<string | null>(null);
  async function createProgram() {
    setError(null);
    try {
      const data = await apiPost<any>("/bug-bounty/programs", { project_name: projectName, scope_summary: scope, in_scope_assets: ["Smart contracts listed in the report", "Public website", "Public API endpoints explicitly listed"], out_of_scope_assets: ["DoS", "social engineering", "credential attacks", "third-party services"], reward_low_inr: 1000, reward_medium_inr: 5000, reward_high_inr: 15000, reward_critical_inr: 50000, contact_email: email, status: "draft", escrow_enabled: false, authorization_confirmed: authorized, real_only_acknowledged: true });
      setResult(data); await loadPrograms();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
  }
  async function loadPrograms() { const data = await apiGet<any>("/bug-bounty/programs"); setPrograms(data.programs || []); }
  async function loadSubmissions(programId?: string) { const suffix = programId ? `?program_id=${encodeURIComponent(programId)}` : ""; const data = await apiGet<any>(`/bug-bounty/submissions${suffix}`); setSubmissions(data.submissions || []); }
  async function createSampleSubmission(programId: string) {
    setError(null);
    try {
      const data = await apiPost<any>("/bug-bounty/submissions", { program_id: programId, researcher_name: "Manual Researcher", researcher_contact: "researcher@example.com", title: "Manual submission for triage", severity_claimed: "medium", affected_asset: "Launch website / contract scope", description: "This is a real stored triage record created from the UI. It is not auto-validated and requires manual review.", reproduction_steps: "Submit safe evidence only. Do not exploit or access third-party systems.", impact: "Potential launch readiness issue requiring manual validation.", authorization_confirmed: true, safe_testing_acknowledged: true, real_only_acknowledged: true });
      setResult(data); await loadSubmissions(programId);
    } catch (err) { setError(err instanceof Error ? err.message : "Submission failed"); }
  }
  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
    <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Mega Phase D • Phase 25</p><h1 className="mt-3 text-3xl font-black sm:text-5xl">Bug Bounty Readiness + Marketplace MVP</h1><p className="mt-4 max-w-3xl text-slate-400">Create real bounty scope, safe-harbor, reward-tier, and researcher submission records. Escrow, auto-validation, and payout automation are not faked.</p>
    <div className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]"><div className="card space-y-4 p-6"><label className="block text-sm font-bold text-slate-200">Project name<input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} /></label><label className="block text-sm font-bold text-slate-200">Scope summary<textarea className="input mt-2 min-h-32" value={scope} onChange={(e) => setScope(e.target.value)} /></label><label className="block text-sm font-bold text-slate-200">Contact email<input className="input mt-2" value={email} onChange={(e) => setEmail(e.target.value)} /></label><label className="flex gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50"><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /><span>I am authorized and understand safe testing limits.</span></label><div className="grid gap-3 sm:grid-cols-2"><button className="btn-secondary" onClick={loadPrograms}>Load programs</button><button className="btn-primary" onClick={createProgram} disabled={!authorized}>Create program</button></div>{error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}</div>
    <div className="space-y-5"><div className="card p-6"><p className="font-black text-white">Programs</p><div className="mt-4 space-y-3">{programs.length ? programs.map((p) => <div key={p.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="font-bold text-white">{p.project_name}</p><p className="text-xs text-slate-400">{p.id} • {p.status} • escrow: {p.escrow_status}</p><div className="mt-3 flex flex-wrap gap-2"><button className="btn-secondary" onClick={() => createSampleSubmission(p.id)}>Create triage record</button><button className="btn-secondary" onClick={() => loadSubmissions(p.id)}>Load submissions</button></div></div>) : <p className="text-sm text-slate-400">No bounty records loaded.</p>}</div></div><div className="card p-6"><p className="font-black text-white">Submissions</p><div className="mt-4 space-y-3">{submissions.length ? submissions.map((s) => <div key={s.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="font-bold text-white">{s.title}</p><p className="text-xs text-slate-400">{s.severity_claimed} • {s.status}</p></div>) : <p className="text-sm text-slate-400">No submissions loaded.</p>}</div></div>{result && <div className="card p-6"><p className="font-black text-white">Latest action</p><div className="mt-4"><JsonBlock value={result} /></div></div>}</div></div>
  </div>;
}
