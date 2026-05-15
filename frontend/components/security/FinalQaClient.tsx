"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type Qa = { launch_readiness: string; security_readiness: string; security_score: number; manual_blockers: string[]; checklist: Array<{ area: string; items: string[] }>; real_only_note: string };
type MapData = { real_live_now: string[]; manual_setup_required: Array<{ service: string; needed_for: string; env_keys: string }>; manual_admin_actions: string[]; never_collect: string[]; real_only_rule: string };

export function FinalQaClient() {
  const [qa, setQa] = useState<Qa | null>(null);
  const [map, setMap] = useState<MapData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([apiGet<Qa>("/final-qa/status"), apiGet<MapData>("/final-qa/implementation-map")])
      .then(([q, m]) => { setQa(q); setMap(m); })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <main className="section"><div className="card border-red-500/30 text-red-100">{error}</div></main>;
  if (!qa || !map) return <main className="section"><div className="card">Loading final QA map...</div></main>;

  return (
    <main className="section space-y-8">
      <section className="hero-grid rounded-[2rem] border border-white/10 bg-white/[0.03] p-8">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Final Production Launch QA</p>
        <h1 className="mt-3 text-4xl font-black text-white md:text-5xl">Implementation Handoff + Launch Readiness</h1>
        <p className="mt-4 max-w-3xl text-slate-300">This page tells what is real now, what needs manual account setup, and what RAADHANEX must verify before public launch. It does not auto-approve production launch.</p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="card"><p className="text-sm text-slate-400">Launch readiness</p><p className="mt-1 text-xl font-black text-white">{qa.launch_readiness}</p></div>
          <div className="card"><p className="text-sm text-slate-400">Security readiness</p><p className="mt-1 text-xl font-black text-white">{qa.security_readiness}</p></div>
          <div className="card"><p className="text-sm text-slate-400">Security score</p><p className="mt-1 text-xl font-black text-cyan">{qa.security_score}/100</p></div>
        </div>
      </section>

      {qa.manual_blockers.length > 0 && <section className="card border-amber-400/30">
        <h2 className="text-2xl font-black text-white">Manual blockers before public launch</h2>
        <ul className="mt-4 space-y-2 text-sm text-amber-100">{qa.manual_blockers.map((b) => <li key={b}>• {b}</li>)}</ul>
      </section>}

      <section className="grid gap-4 lg:grid-cols-2">
        {qa.checklist.map((group) => (
          <article className="card" key={group.area}>
            <h2 className="text-xl font-black text-white">{group.area}</h2>
            <ul className="mt-4 space-y-2 text-sm text-slate-300">{group.items.map((item) => <li key={item}>• {item}</li>)}</ul>
          </article>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="card">
          <h2 className="text-2xl font-black text-white">Real live now</h2>
          <ul className="mt-4 space-y-2 text-sm text-slate-300">{map.real_live_now.map((item) => <li key={item}>• {item}</li>)}</ul>
        </article>
        <article className="card">
          <h2 className="text-2xl font-black text-white">Never collect</h2>
          <ul className="mt-4 space-y-2 text-sm text-red-100">{map.never_collect.map((item) => <li key={item}>• {item}</li>)}</ul>
        </article>
      </section>

      <section className="card">
        <h2 className="text-2xl font-black text-white">Manual accounts and env keys</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400"><tr><th className="py-2">Service</th><th>Needed for</th><th>Env keys</th></tr></thead>
            <tbody>{map.manual_setup_required.map((acc) => <tr className="border-t border-white/10" key={acc.service}><td className="py-3 font-bold text-white">{acc.service}</td><td className="text-slate-300">{acc.needed_for}</td><td className="font-mono text-xs text-cyan">{acc.env_keys}</td></tr>)}</tbody>
          </table>
        </div>
      </section>

      <section className="card border-cyan/20"><p className="text-slate-300">{map.real_only_rule}</p><p className="mt-2 text-sm text-slate-500">{qa.real_only_note}</p></section>
    </main>
  );
}
