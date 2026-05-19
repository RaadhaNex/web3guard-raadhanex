"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type JourneyStep = {
  step: number;
  label: string;
  route: string;
  primary_action: string;
  success_state: string;
};

type AdvancedArea = {
  group: string;
  routes: string[];
  why_hidden: string;
};

type JourneyPayload = {
  ok: boolean;
  phase: string;
  journey: JourneyStep[];
  advanced_areas: AdvancedArea[];
  first_user_rule: string;
  do_not_add_to_primary_nav: string[];
};

type StateCopyPayload = {
  ok: boolean;
  phase: string;
  states: Record<string, { headline: string; user_copy: string; next_action: string }>;
  ux_rule: string;
};

type ChecklistPayload = {
  ok: boolean;
  phase: string;
  goal: string;
  checklist: Array<{ item: string; status: string; evidence: string }>;
  next_manual_step: string;
};

type FeedbackResponse = {
  ok: boolean;
  accepted: boolean;
  feedback_id?: string;
  reason?: string;
  message?: string;
};

type ClaimCheckResponse = {
  allowed: boolean;
  blocked_terms: string[];
  safe_replacement: string;
};

const defaultFeedback = "Results page was useful, but I want a clearer next step after Tool Not Installed.";
const defaultClaimText = "Web3Guard is a pre-audit readiness scanner, not a certified audit.";

function badgeClass(status: string) {
  if (status === "Ready") return "badge badge-cyan";
  if (status.includes("Blocked")) return "badge badge-red";
  return "badge";
}

export function PilotExperienceClient() {
  const [journey, setJourney] = useState<JourneyPayload | null>(null);
  const [stateCopy, setStateCopy] = useState<StateCopyPayload | null>(null);
  const [checklist, setChecklist] = useState<ChecklistPayload | null>(null);
  const [message, setMessage] = useState(defaultFeedback);
  const [pagePath, setPagePath] = useState("/results");
  const [frictionArea, setFrictionArea] = useState("result clarity");
  const [role, setRole] = useState("founder");
  const [feedback, setFeedback] = useState<FeedbackResponse | null>(null);
  const [claimText, setClaimText] = useState(defaultClaimText);
  const [claimResult, setClaimResult] = useState<ClaimCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiGet<JourneyPayload>("/pilot-experience/journey"),
      apiGet<StateCopyPayload>("/pilot-experience/state-copy"),
      apiGet<ChecklistPayload>("/pilot-experience/conversion-checklist"),
    ])
      .then(([journeyPayload, statePayload, checklistPayload]) => {
        setJourney(journeyPayload);
        setStateCopy(statePayload);
        setChecklist(checklistPayload);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const visiblePathSummary = useMemo(() => {
    if (!journey) return "Loading first-user journey...";
    return journey.journey.map((step) => step.label).join(" → ");
  }, [journey]);

  async function submitFeedback() {
    setError(null);
    setFeedback(null);
    try {
      const response = await apiPost<FeedbackResponse>("/pilot-experience/feedback", {
        page_path: pagePath,
        role,
        friction_area: frictionArea,
        message,
        can_contact: false,
      });
      setFeedback(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feedback failed");
    }
  }

  async function runClaimCheck() {
    setError(null);
    setClaimResult(null);
    try {
      const response = await apiPost<ClaimCheckResponse>("/pilot-experience/claim-check", { text: claimText });
      setClaimResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    }
  }

  return (
    <div className="mt-10 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
      <section className="card p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="section-label">Pilot journey</p>
            <h2 className="mt-2 text-2xl font-black text-white">Seven paths, one conversion flow</h2>
          </div>
          <span className="badge badge-cyan">No feature removal</span>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-400">{visiblePathSummary}</p>

        <div className="mt-5 grid gap-3">
          {journey?.journey.map((step) => (
            <Link key={step.route} href={step.route} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 transition hover:border-cyan/25 hover:bg-cyan/[0.04]">
              <div className="flex flex-wrap items-center gap-3">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-cyan/10 text-sm font-black text-cyan">{step.step}</span>
                <p className="text-lg font-black text-white">{step.label}</p>
                <span className="text-xs text-slate-500">{step.route}</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{step.primary_action}</p>
              <p className="mt-2 text-xs leading-5 text-slate-500">Success: {step.success_state}</p>
            </Link>
          ))}
        </div>

        <div className="mt-5 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4">
          <p className="font-black text-amber-100">Advanced pages stay available, but not in primary nav</p>
          <div className="mt-3 grid gap-3">
            {journey?.advanced_areas.map((area) => (
              <div key={area.group} className="rounded-xl border border-white/[0.08] bg-black/20 p-3">
                <p className="font-bold text-white">{area.group}</p>
                <p className="mt-1 text-sm leading-6 text-amber-100/80">{area.why_hidden}</p>
                <p className="mt-2 text-xs text-slate-500">{area.routes.join(", ")}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5">
        <div className="card p-5 sm:p-6">
          <p className="section-label">Cleaner status copy</p>
          <h2 className="mt-2 text-2xl font-black text-white">Setup gaps are not findings</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">{stateCopy?.ux_rule || "Loading UX rule..."}</p>
          <div className="mt-5 grid gap-3">
            {stateCopy ? Object.entries(stateCopy.states).map(([state, copy]) => (
              <div key={state} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge">{state}</span>
                  <p className="font-black text-white">{copy.headline}</p>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">{copy.user_copy}</p>
                <p className="mt-2 text-xs leading-5 text-cyan/90">Next: {copy.next_action}</p>
              </div>
            )) : null}
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <p className="section-label">First 10 users</p>
          <h2 className="mt-2 text-2xl font-black text-white">Conversion checklist</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">{checklist?.goal || "Loading checklist..."}</p>
          <div className="mt-5 grid gap-3">
            {checklist?.checklist.map((item) => (
              <div key={item.item} className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={badgeClass(item.status)}>{item.status}</span>
                  <p className="font-bold text-white">{item.item}</p>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{item.evidence}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="card p-5 sm:p-6 lg:col-span-2">
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <p className="section-label">Feedback intake</p>
            <h2 className="mt-2 text-2xl font-black text-white">Collect pilot friction without secrets</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">Feedback is stored locally by this patch. Private keys, seed phrases, mnemonics, and secret-like values are rejected.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <input value={pagePath} onChange={(event) => setPagePath(event.target.value)} className="rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-cyan/40" />
              <input value={role} onChange={(event) => setRole(event.target.value)} className="rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-cyan/40" />
              <input value={frictionArea} onChange={(event) => setFrictionArea(event.target.value)} className="rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-cyan/40" />
            </div>
            <textarea value={message} onChange={(event) => setMessage(event.target.value)} rows={5} className="mt-3 w-full rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm text-slate-200 outline-none focus:border-cyan/40" />
            <button type="button" onClick={submitFeedback} className="btn-primary mt-3">Save pilot feedback</button>
            {feedback ? <p className={`mt-3 rounded-xl border p-3 text-sm ${feedback.accepted ? "border-cyan/20 bg-cyan/[0.06] text-cyan" : "border-red-400/20 bg-red-400/10 text-red-100"}`}>{feedback.message || feedback.reason || feedback.feedback_id}</p> : null}
          </div>

          <div>
            <p className="section-label">Copy guard</p>
            <h2 className="mt-2 text-2xl font-black text-white">Check launch wording before publishing</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">Use this before outreach pages, reports, posts, or pricing copy. It blocks fake audit/security/payment claims.</p>
            <textarea value={claimText} onChange={(event) => setClaimText(event.target.value)} rows={6} className="mt-5 w-full rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm text-slate-200 outline-none focus:border-cyan/40" />
            <button type="button" onClick={runClaimCheck} className="btn-secondary mt-3">Check copy</button>
            {claimResult ? (
              <div className={`mt-3 rounded-xl border p-4 text-sm ${claimResult.allowed ? "border-cyan/20 bg-cyan/[0.06] text-cyan" : "border-red-400/20 bg-red-400/10 text-red-100"}`}>
                <p className="font-black">{claimResult.allowed ? "Allowed" : "Blocked"}</p>
                <p className="mt-2">{claimResult.allowed ? "No unsafe claim pattern detected." : `Blocked: ${claimResult.blocked_terms.join(", ")}`}</p>
                <p className="mt-2 text-xs opacity-80">Safe wording: {claimResult.safe_replacement}</p>
              </div>
            ) : null}
            {error ? <p className="mt-3 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</p> : null}
          </div>
        </div>
      </section>
    </div>
  );
}
