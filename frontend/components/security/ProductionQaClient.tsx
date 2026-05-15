"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type AnyObj = Record<string, any>;
function Pill({ ok }: { ok?: boolean }) { return <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${ok ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-100" : "border-amber-400/30 bg-amber-500/10 text-amber-100"}`}>{ok ? "configured" : "manual needed"}</span>; }
function JsonBlock({ value }: { value: unknown }) { return <pre className="mono max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>; }
export function ProductionQaClient() {
  const [status, setStatus] = useState<AnyObj | null>(null); const [checklist, setChecklist] = useState<AnyObj | null>(null); const [accounts, setAccounts] = useState<AnyObj | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(()=>{ Promise.all([apiGet<AnyObj>("/production-qa/status"), apiGet<AnyObj>("/production-qa/final-checklist"), apiGet<AnyObj>("/production-qa/account-setup")]).then(([a,b,c])=>{ setStatus(a); setChecklist(b); setAccounts(c); }).catch(e=>setError(e.message)); },[]);
  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
    <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Mega Phase G • Phase 35</p>
    <h1 className="mt-3 text-3xl font-black sm:text-5xl">Final Production Launch QA</h1>
    <p className="mt-4 max-w-3xl text-slate-400">Final handoff map for running the MVP as a real platform. It clearly separates configured/live services from manual setup required.</p>
    {error && <p className="mt-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
    <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <section className="space-y-5">
        <div className="card p-5"><div className="flex items-center justify-between gap-3"><p className="font-black text-white">Production status</p><Pill ok={status?.production_ready} /></div><div className="mt-4"><JsonBlock value={status || { loading: true }} /></div></div>
        <div className="card p-5"><p className="font-black text-white">Manual accounts/env setup</p><div className="mt-4 space-y-3">{accounts?.accounts?.map((a: AnyObj) => <div key={a.service} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><div className="flex flex-wrap items-center justify-between gap-3"><p className="font-bold text-white">{a.service}</p><Pill ok={a.configured} /></div><p className="mt-2 text-sm text-slate-400">{a.purpose}</p><p className="mt-2 text-xs text-slate-500">Env/manual: {a.env?.join(", ")}</p></div>)}</div></div>
      </section>
      <section className="card p-5"><p className="font-black text-white">Final checklist</p><div className="mt-5 space-y-4">{checklist?.checklist?.map((group: AnyObj) => <div key={group.area} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="font-bold text-cyan">{group.area}</p><ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">{group.items?.map((item: string) => <li key={item}>{item}</li>)}</ul></div>)}</div></section>
    </div>
  </div>;
}
