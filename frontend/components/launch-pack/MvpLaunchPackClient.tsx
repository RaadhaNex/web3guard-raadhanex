"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type StatusPayload = {
  ok: boolean;
  phase: string;
  status: string;
  build_phase_status: string;
  primary_goal: string;
  visible_user_path: string[];
  no_fake_claims: boolean;
};

type ChecklistGroup = {
  group: string;
  items: string[];
};

type ChecklistPayload = {
  ok: boolean;
  phase: string;
  checklist: ChecklistGroup[];
  exit_criteria: string[];
};

type OutreachTemplate = {
  channel: string;
  audience: string;
  message: string;
  cta: string;
};

type OutreachPayload = {
  ok: boolean;
  phase: string;
  templates: OutreachTemplate[];
  daily_action_plan: string[];
  target_segments: string[];
};

type SampleReportPayload = {
  ok: boolean;
  phase: string;
  template: {
    title: string;
    required_sections: string[];
    safe_opening_copy: string;
    safe_close_copy: string;
  };
  report_price_anchor_inr: number;
  payment_truth_rule: string;
};

type PublicBetaPayload = {
  ok: boolean;
  phase: string;
  product_hunt_prep: string[];
  public_beta_assets: string[];
  do_not_launch_if: string[];
};

type GuidancePayload = {
  ok: boolean;
  phase: string;
  what_to_say: string[];
  what_not_to_claim: string[];
  positioning: string;
};

type TrackerPayload = {
  ok: boolean;
  phase: string;
  target_count: number;
  current_count: number;
  remaining: number;
  records: Array<Record<string, string | null>>;
  next_rule: string;
};

type TrackerResponse = {
  ok: boolean;
  accepted: boolean;
  pilot_id?: string;
  current_count?: number;
  remaining?: number;
  reason?: string;
  message?: string;
};

type ClaimCheckResponse = {
  allowed: boolean;
  blocked_terms: string[];
  safe_replacement: string;
};

const defaultClaimText = "Web3Guard AI is a pre-audit launch readiness scanner, not a certified audit.";
const defaultTracker = {
  project_name: "Pilot dApp Alpha",
  founder_segment: "hackathon team",
  source_channel: "ETHIndia Discord",
  stage: "report requested",
  paid_intent: "maybe ₹999",
  highest_friction: "Needs clearer next step after Not Assessed modules",
  next_action: "send pilot report sample",
};

function smallBadge(text: string, tone: "cyan" | "amber" | "red" | "slate" = "slate") {
  const toneClass =
    tone === "cyan"
      ? "border-cyan/20 bg-cyan/[0.08] text-cyan"
      : tone === "amber"
        ? "border-amber-300/20 bg-amber-300/10 text-amber-100"
        : tone === "red"
          ? "border-red-400/20 bg-red-400/10 text-red-100"
          : "border-white/[0.08] bg-white/[0.04] text-slate-300";
  return <span className={`rounded-full border px-3 py-1 text-[11px] font-black uppercase tracking-[0.14em] ${toneClass}`}>{text}</span>;
}

export function MvpLaunchPackClient() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [checklist, setChecklist] = useState<ChecklistPayload | null>(null);
  const [outreach, setOutreach] = useState<OutreachPayload | null>(null);
  const [sampleReport, setSampleReport] = useState<SampleReportPayload | null>(null);
  const [publicBeta, setPublicBeta] = useState<PublicBetaPayload | null>(null);
  const [guidance, setGuidance] = useState<GuidancePayload | null>(null);
  const [tracker, setTracker] = useState<TrackerPayload | null>(null);
  const [trackerForm, setTrackerForm] = useState(defaultTracker);
  const [trackerResult, setTrackerResult] = useState<TrackerResponse | null>(null);
  const [claimText, setClaimText] = useState(defaultClaimText);
  const [claimResult, setClaimResult] = useState<ClaimCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadAll() {
    const [statusPayload, checklistPayload, outreachPayload, samplePayload, betaPayload, guidancePayload, trackerPayload] = await Promise.all([
      apiGet<StatusPayload>("/mvp-launch/status"),
      apiGet<ChecklistPayload>("/mvp-launch/launch-checklist"),
      apiGet<OutreachPayload>("/mvp-launch/outreach-kit"),
      apiGet<SampleReportPayload>("/mvp-launch/sample-report"),
      apiGet<PublicBetaPayload>("/mvp-launch/public-beta-checklist"),
      apiGet<GuidancePayload>("/mvp-launch/claim-guidance"),
      apiGet<TrackerPayload>("/mvp-launch/first-10"),
    ]);
    setStatus(statusPayload);
    setChecklist(checklistPayload);
    setOutreach(outreachPayload);
    setSampleReport(samplePayload);
    setPublicBeta(betaPayload);
    setGuidance(guidancePayload);
    setTracker(trackerPayload);
  }

  useEffect(() => {
    loadAll().catch((err: Error) => setError(err.message));
  }, []);

  const pathSummary = useMemo(() => status?.visible_user_path.join(" → ") || "Scanner → Results → Fix Plan → Report → Pricing → Dashboard → Docs", [status]);

  async function savePilotUser() {
    setError(null);
    setTrackerResult(null);
    try {
      const response = await apiPost<TrackerResponse>("/mvp-launch/first-10", trackerForm);
      setTrackerResult(response);
      const latest = await apiGet<TrackerPayload>("/mvp-launch/first-10");
      setTracker(latest);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pilot tracker failed");
    }
  }

  async function runClaimCheck() {
    setError(null);
    setClaimResult(null);
    try {
      const response = await apiPost<ClaimCheckResponse>("/mvp-launch/claim-check", { text: claimText });
      setClaimResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    }
  }

  function updateTrackerField(field: keyof typeof defaultTracker, value: string) {
    setTrackerForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <div className="mt-10 grid gap-6">
      {error ? <div className="rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-100">{error}</div> : null}

      <section className="grid gap-5 lg:grid-cols-3">
        <div className="card p-5 sm:p-6 lg:col-span-2">
          <div className="flex flex-wrap gap-2">
            {smallBadge("MVP launch pack", "cyan")}
            {smallBadge("last build phase", "amber")}
            {smallBadge("no fake claims", "red")}
          </div>
          <h2 className="mt-4 text-3xl font-black text-white">Stop building random phases. Launch, learn, and validate.</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">{status?.build_phase_status || "Apply, test, deploy, and get the first 10 founder sessions before adding more feature pages."}</p>
          <p className="mt-4 rounded-2xl border border-cyan/15 bg-cyan/[0.06] p-4 text-sm font-bold leading-6 text-cyan">{pathSummary}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Start scan</Link>
            <Link href="/results" className="btn-secondary">View results</Link>
            <Link href="/payment-validation" className="btn-secondary">Payment validation</Link>
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <p className="section-label">First 10 users</p>
          <h3 className="mt-2 text-2xl font-black text-white">{tracker?.current_count ?? 0}/{tracker?.target_count ?? 10} tracked</h3>
          <p className="mt-3 text-sm leading-6 text-slate-400">{tracker?.next_rule || "Use real pilot friction to decide what to fix next."}</p>
          <div className="mt-5 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
            <p className="text-sm text-slate-400">Remaining</p>
            <p className="mt-1 text-4xl font-black text-cyan">{tracker?.remaining ?? 10}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="card p-5 sm:p-6">
          <p className="section-label">Launch checklist</p>
          <h2 className="mt-2 text-2xl font-black text-white">Final ship gates before public beta</h2>
          <div className="mt-5 grid gap-4">
            {checklist?.checklist.map((group) => (
              <div key={group.group} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                <h3 className="font-black text-white">{group.group}</h3>
                <ol className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
                  {group.items.map((item, index) => <li key={item}><span className="text-cyan">{index + 1}.</span> {item}</li>)}
                </ol>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <p className="section-label">Exit criteria</p>
          <h2 className="mt-2 text-2xl font-black text-white">No launch if these fail</h2>
          <div className="mt-5 grid gap-3">
            {checklist?.exit_criteria.map((item) => (
              <div key={item} className="rounded-xl border border-white/[0.08] bg-black/20 p-3 text-sm leading-6 text-slate-300">✓ {item}</div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="card p-5 sm:p-6 lg:col-span-2">
          <p className="section-label">Outreach kit</p>
          <h2 className="mt-2 text-2xl font-black text-white">Messages for the first 10 real users</h2>
          <div className="mt-5 grid gap-4">
            {outreach?.templates.map((template) => (
              <div key={template.channel} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                <div className="flex flex-wrap gap-2">
                  {smallBadge(template.channel, "cyan")}
                  {smallBadge(template.audience)}
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-300">{template.message}</p>
                <p className="mt-3 text-xs font-bold text-cyan">CTA: {template.cta}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <p className="section-label">Daily action</p>
          <h2 className="mt-2 text-2xl font-black text-white">Do this, not more phases</h2>
          <div className="mt-5 grid gap-3">
            {outreach?.daily_action_plan.map((item) => (
              <div key={item} className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-3 text-sm leading-6 text-slate-300">{item}</div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="card p-5 sm:p-6">
          <p className="section-label">Pilot tracker</p>
          <h2 className="mt-2 text-2xl font-black text-white">Save first-user friction safely</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">Do not paste private keys, seed phrases, API keys, access tokens, or secrets. This patch stores local JSONL only.</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {(Object.keys(defaultTracker) as Array<keyof typeof defaultTracker>).map((field) => (
              <label key={field} className="grid gap-2 text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
                {field.replaceAll("_", " ")}
                <input value={trackerForm[field]} onChange={(event) => updateTrackerField(field, event.target.value)} className="rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm normal-case tracking-normal text-white outline-none focus:border-cyan/40" />
              </label>
            ))}
          </div>
          <button type="button" onClick={savePilotUser} className="btn-primary mt-4">Save pilot user</button>
          {trackerResult ? <p className={`mt-3 rounded-xl border p-3 text-sm ${trackerResult.accepted ? "border-cyan/20 bg-cyan/[0.06] text-cyan" : "border-red-400/20 bg-red-400/10 text-red-100"}`}>{trackerResult.message || trackerResult.reason || trackerResult.pilot_id}</p> : null}
        </div>

        <div className="card p-5 sm:p-6">
          <p className="section-label">Recent pilot records</p>
          <h2 className="mt-2 text-2xl font-black text-white">Evidence before roadmap</h2>
          <div className="mt-5 grid gap-3">
            {tracker?.records.length ? tracker.records.map((record) => (
              <div key={String(record.pilot_id)} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                <div className="flex flex-wrap items-center gap-2">
                  {smallBadge(String(record.stage || "tracked"), "cyan")}
                  <p className="font-black text-white">{record.project_name}</p>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">Friction: {record.highest_friction}</p>
                <p className="mt-2 text-xs text-cyan">Next: {record.next_action}</p>
              </div>
            )) : <p className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 text-sm text-slate-400">No pilot records yet. Add the first real founder conversation.</p>}
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card p-5 sm:p-6">
          <p className="section-label">Pilot report template</p>
          <h2 className="mt-2 text-2xl font-black text-white">₹{sampleReport?.report_price_anchor_inr || 999} first paid report anchor</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">{sampleReport?.template.safe_opening_copy}</p>
          <div className="mt-5 grid gap-2">
            {sampleReport?.template.required_sections.map((section) => (
              <div key={section} className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-3 text-sm text-slate-300">{section}</div>
            ))}
          </div>
          <p className="mt-4 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm leading-6 text-amber-100">{sampleReport?.payment_truth_rule}</p>
        </div>

        <div className="card p-5 sm:p-6">
          <p className="section-label">Public beta</p>
          <h2 className="mt-2 text-2xl font-black text-white">Launch assets and blockers</h2>
          <div className="mt-5 grid gap-4">
            <div>
              <p className="font-black text-white">Prepare</p>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
                {publicBeta?.product_hunt_prep.map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
            <div className="rounded-2xl border border-red-400/20 bg-red-400/10 p-4">
              <p className="font-black text-red-100">Do not launch if</p>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-red-50/90">
                {publicBeta?.do_not_launch_if.map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card p-5 sm:p-6">
          <p className="section-label">What to say</p>
          <h2 className="mt-2 text-2xl font-black text-white">Position honestly</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">{guidance?.positioning}</p>
          <div className="mt-5 grid gap-3">
            {guidance?.what_to_say.map((item) => <div key={item} className="rounded-xl border border-cyan/15 bg-cyan/[0.05] p-3 text-sm leading-6 text-cyan">{item}</div>)}
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <p className="section-label">Claim checker</p>
          <h2 className="mt-2 text-2xl font-black text-white">Block unsafe launch copy</h2>
          <textarea value={claimText} onChange={(event) => setClaimText(event.target.value)} rows={5} className="mt-5 w-full rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm text-slate-200 outline-none focus:border-cyan/40" />
          <button type="button" onClick={runClaimCheck} className="btn-primary mt-3">Check claim</button>
          {claimResult ? (
            <div className={`mt-4 rounded-2xl border p-4 text-sm ${claimResult.allowed ? "border-cyan/20 bg-cyan/[0.06] text-cyan" : "border-red-400/20 bg-red-400/10 text-red-100"}`}>
              <p className="font-black">{claimResult.allowed ? "Allowed" : "Blocked"}</p>
              <p className="mt-2">{claimResult.allowed ? claimResult.safe_replacement : `Blocked terms: ${claimResult.blocked_terms.join(", ")}`}</p>
            </div>
          ) : null}
          <div className="mt-5 grid gap-2">
            {guidance?.what_not_to_claim.map((item) => <div key={item} className="rounded-xl border border-red-400/15 bg-red-400/[0.06] p-3 text-sm leading-6 text-red-50/90">{item}</div>)}
          </div>
        </div>
      </section>
    </div>
  );
}
