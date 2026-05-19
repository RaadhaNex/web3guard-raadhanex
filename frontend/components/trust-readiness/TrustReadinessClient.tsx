"use client";

import { useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";

const demoUser = "demo-user";

type ComponentScore = {
  id: string;
  label: string;
  weight: number;
  description: string;
  score: number;
  status: string;
  evidence_count: number;
  max_evidence: number;
  reasons: string[];
  next_actions: string[];
};

type ReadinessScore = {
  ok: boolean;
  generated_at: string;
  user_id: string;
  project_id: string | null;
  score: number;
  label: string;
  score_type: string;
  component_scores: ComponentScore[];
  summary: Record<string, number>;
  priority_actions: Array<{ component: string; action: string; score: number; status: string }>;
  project_options: Array<{ id: string; name: string; website_url?: string | null; chain?: string | null; project_type?: string | null }>;
  safe_public_wording: string;
  blocked_wording: string[];
  real_only_note: string;
  boundaries: string[];
};

function statusTone(status: string) {
  const value = status.toLowerCase();
  if (value.includes("strong")) return "badge-green";
  if (value.includes("improving")) return "badge-cyan";
  if (value.includes("evidence")) return "badge-amber";
  return "badge-red";
}

function scoreTone(score: number) {
  if (score >= 80) return "text-emerald-200";
  if (score >= 60) return "text-cyan";
  if (score >= 40) return "text-amber-200";
  return "text-red-200";
}

function ScoreRing({ score }: { score: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative h-40 w-40 shrink-0">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 140 140" aria-label={`Readiness score ${score}`}>
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="12" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={scoreTone(score)}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <p className={`text-4xl font-black ${scoreTone(score)}`}>{score}</p>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">/ 100</p>
        </div>
      </div>
    </div>
  );
}

export function TrustReadinessClient() {
  const [userId, setUserId] = useState(demoUser);
  const [projectId, setProjectId] = useState("");
  const [data, setData] = useState<ReadinessScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadScore() {
    const cleanUserId = userId.trim();
    if (!cleanUserId) {
      setError("Enter a user_id to load stored readiness evidence.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ user_id: cleanUserId });
      if (projectId.trim()) qs.set("project_id", projectId.trim());
      const result = await apiGet<ReadinessScore>(`/trust-readiness/score?${qs.toString()}`);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load readiness score.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative overflow-hidden">
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <p className="section-label">Founder Trust Score</p>
            <h1 className="mt-4 text-4xl font-black tracking-[-0.06em] sm:text-6xl">Launch Trust Readiness, without audit-score confusion.</h1>
            <p className="mt-5 max-w-3xl text-base leading-8 text-slate-400">
              This score helps founders understand launch readiness across evidence, fixes, transparency, wallet safety, GitHub hygiene, admin OpSec, report verification, monitoring, and bounty readiness. It is not a certified audit.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/eon" className="btn-secondary">Open EON risk graph</Link>
              <Link href="/trust-pages" className="btn-secondary">Public trust pages</Link>
              <Link href="/continuous-monitoring" className="btn-secondary">Monitoring</Link>
            </div>
          </div>

          <div className="scan-door-shell min-h-0">
            <div className="scan-door-left" />
            <div className="scan-door-right" />
            <div className="holo-orb" />
            <div className="scan-door-label mono">readiness engine</div>
            <div className="relative z-[2] pt-10">
              <div className="terminal-card rounded-[24px] p-5">
                <div className="grid gap-4 sm:grid-cols-[1fr_0.7fr]">
                  <label className="grid gap-2 text-sm font-bold text-slate-300">
                    User ID
                    <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="Supabase/local user_id" />
                  </label>
                  <label className="grid gap-2 text-sm font-bold text-slate-300">
                    Project ID optional
                    <input className="input" value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="project_id" />
                  </label>
                </div>
                <button className="btn-primary mt-4 w-full" onClick={() => void loadScore()} disabled={loading}>
                  {loading ? "Loading readiness..." : "Calculate readiness"}
                </button>
                {error ? <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}
                <p className="mt-4 text-xs leading-5 text-slate-500">
                  Score is generated only from stored records. Empty results mean no evidence yet, not a hidden pass.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {data ? (
        <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
          <div className="grid gap-6 lg:grid-cols-[0.82fr_1.18fr]">
            <div className="quantum-stage p-6">
              <div className="flex flex-col items-center gap-5 text-center">
                <ScoreRing score={data.score} />
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">{data.score_type}</p>
                  <h2 className="mt-2 text-3xl font-black text-white">{data.label}</h2>
                  <p className="mt-3 text-sm leading-7 text-slate-400">{data.real_only_note}</p>
                </div>
              </div>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {Object.entries(data.summary).map(([key, value]) => (
                  <div key={key} className="stat-slab p-4">
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{key.replace(/_/g, " ")}</p>
                    <p className="mt-2 text-2xl font-black text-white">{value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4">
              {data.component_scores.map((component) => (
                <div key={component.id} className="glass-tile p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-lg font-black text-white">{component.label}</p>
                      <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-400">{component.description}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-black ${scoreTone(component.score)}`}>{component.score}</p>
                      <span className={`badge ${statusTone(component.status)}`}>{component.status.replace(/_/g, " ")}</span>
                    </div>
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.06]">
                    <div className="h-full rounded-full bg-gradient-to-r from-cyan to-purple-400" style={{ width: `${component.score}%` }} />
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-slate-300">
                      <p className="font-black text-white">Why</p>
                      <ul className="mt-2 space-y-1">
                        {component.reasons.map((reason) => <li key={reason}>• {reason}</li>)}
                      </ul>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-slate-300">
                      <p className="font-black text-white">Next action</p>
                      {component.next_actions.length ? (
                        <ul className="mt-2 space-y-1">{component.next_actions.map((action) => <li key={action}>• {action}</li>)}</ul>
                      ) : (
                        <p className="mt-2 text-slate-500">Keep evidence fresh and re-run before launch.</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="glass-tile p-6">
              <h2 className="text-2xl font-black text-white">Priority action plan</h2>
              <div className="mt-5 grid gap-3">
                {data.priority_actions.length ? data.priority_actions.map((item, index) => (
                  <div key={`${item.component}-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="text-sm font-black text-cyan">{item.component}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-300">{item.action}</p>
                    <p className="mt-2 text-xs text-slate-500">Status: {item.status} · Component score: {item.score}</p>
                  </div>
                )) : <p className="text-sm text-slate-500">No priority actions were generated from stored records.</p>}
              </div>
            </div>

            <div className="glass-tile p-6">
              <h2 className="text-2xl font-black text-white">Safe public wording</h2>
              <p className="mt-3 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm font-bold text-emerald-100">{data.safe_public_wording}</p>
              <p className="mt-5 text-sm font-black text-white">Never use these claims</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {data.blocked_wording.map((word) => <span key={word} className="badge badge-red">{word}</span>)}
              </div>
              <div className="mt-5 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
                {data.boundaries.map((boundary) => <p key={boundary}>• {boundary}</p>)}
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}
