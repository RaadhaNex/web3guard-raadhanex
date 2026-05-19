"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";

type LaunchGate = {
  key: string;
  area: string;
  label: string;
  status: string;
  severity: string;
  passed: boolean;
  evidence: string;
  action: string;
};

type ReleaseStatus = {
  ok: boolean;
  version: string;
  release_readiness: string;
  passed_gates: number;
  total_gates: number;
  manual_approval_required: boolean;
  critical_blocker_count: number;
  high_blocker_count: number;
  gates: LaunchGate[];
  remaining_high_priority_count: number;
  safe_release_wording: string;
  safe_missing_labels: string[];
  never_collect: string[];
  not_claimed: string[];
};

type ChecklistSection = {
  area: string;
  required: boolean;
  items: string[];
};

type ChecklistResponse = {
  ok: boolean;
  version: string;
  sections: ChecklistSection[];
};

type DeployPlan = {
  ok: boolean;
  commands: Record<string, string[]>;
  live_checks: { target: string; check: string }[];
};

type ReleaseNotes = {
  ok: boolean;
  title: string;
  safe_intro: string;
  included_layers: string[];
  not_claimed: string[];
  release_gate: string;
};

type RemainingItem = {
  area: string;
  priority: string;
  work: string;
};

type RemainingResponse = {
  ok: boolean;
  summary: string;
  remaining_work: {
    area: string;
    status: string;
    priority: string;
    remaining_work: string;
    how_to_complete: string;
    verify: string;
  }[];
  next_deep_workstreams: RemainingItem[];
};

type ClaimCheck = {
  ok: boolean;
  safe: boolean;
  blocked_claim?: string | null;
  safe_release_wording: string;
  rewrite_hint?: string | null;
};

function classForSeverity(severity: string) {
  const normalized = severity.toLowerCase();
  if (normalized === "critical") return "border-red-400/25 bg-red-500/10 text-red-100";
  if (normalized === "high") return "border-orange-400/25 bg-orange-500/10 text-orange-100";
  if (normalized === "medium") return "border-amber-300/25 bg-amber-400/10 text-amber-100";
  return "border-cyan/20 bg-cyan/10 text-cyan-50";
}

function GateCard({ gate }: { gate: LaunchGate }) {
  return (
    <article className="glass-tile p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">{gate.area}</p>
          <h3 className="mt-2 text-lg font-black text-white">{gate.label}</h3>
        </div>
        <StatusPill status={gate.passed ? "Pass" : gate.status} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className={`rounded-full border px-3 py-1 text-xs font-black uppercase tracking-[0.14em] ${classForSeverity(gate.severity)}`}>{gate.severity}</span>
        <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-slate-300">{gate.key.replaceAll("_", " ")}</span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-400">{gate.evidence}</p>
      <p className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-sm leading-6 text-slate-300">{gate.action}</p>
    </article>
  );
}

function CommandBlock({ title, commands }: { title: string; commands: string[] }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">{title}</p>
      <div className="mt-3 grid gap-2">
        {commands.map((command) => (
          <code key={command} className="block overflow-x-auto rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-cyan">
            {command}
          </code>
        ))}
      </div>
    </div>
  );
}

export function LaunchFinalClient() {
  const [status, setStatus] = useState<ReleaseStatus | null>(null);
  const [checklist, setChecklist] = useState<ChecklistResponse | null>(null);
  const [deployPlan, setDeployPlan] = useState<DeployPlan | null>(null);
  const [releaseNotes, setReleaseNotes] = useState<ReleaseNotes | null>(null);
  const [remaining, setRemaining] = useState<RemainingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [claimText, setClaimText] = useState("Web3Guard AI provides pre-audit launch readiness evidence and Not Assessed labels for missing providers.");
  const [claimResult, setClaimResult] = useState<ClaimCheck | null>(null);
  const [checkingClaim, setCheckingClaim] = useState(false);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [statusData, checklistData, deployData, notesData, remainingData] = await Promise.all([
        apiGet<ReleaseStatus>("/launch-final/status"),
        apiGet<ChecklistResponse>("/launch-final/public-release-checklist"),
        apiGet<DeployPlan>("/launch-final/deploy-verification"),
        apiGet<ReleaseNotes>("/launch-final/release-notes"),
        apiGet<RemainingResponse>("/launch-final/remaining-work"),
      ]);
      setStatus(statusData);
      setChecklist(checklistData);
      setDeployPlan(deployData);
      setReleaseNotes(notesData);
      setRemaining(remainingData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load launch final QA data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  const blockedGateCount = useMemo(() => {
    if (!status) return 0;
    return status.gates.filter((gate) => !gate.passed).length;
  }, [status]);

  async function checkClaim(event: FormEvent) {
    event.preventDefault();
    setCheckingClaim(true);
    setClaimResult(null);
    setError(null);
    try {
      const data = await apiPost<ClaimCheck>("/launch-final/claim-check", { text: claimText });
      setClaimResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed.");
    } finally {
      setCheckingClaim(false);
    }
  }

  if (loading) {
    return <section className="mt-6"><CommandLoadingState label="Loading launch final QA gates..." /></section>;
  }

  if (error) {
    return <section className="mt-6"><CommandNotice tone="danger" title="Launch final QA could not load" text={error} /></section>;
  }

  if (!status || !checklist || !deployPlan || !releaseNotes || !remaining) {
    return <section className="mt-6"><CommandNotice tone="warning" title="Launch final QA unavailable" text="The backend did not return the expected launch-final payload." /></section>;
  }

  return (
    <section className="mt-6 space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Release gate</p>
          <p className="mt-2 text-2xl font-black text-white">{status.release_readiness.replaceAll("_", " ")}</p>
          <p className="mt-2 text-sm text-slate-400">Not a certified audit or 100% secure claim.</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Passed gates</p>
          <p className="mt-2 text-3xl font-black text-white">{status.passed_gates}/{status.total_gates}</p>
          <p className="mt-2 text-sm text-slate-400">{blockedGateCount} action item(s) remain.</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Critical / high</p>
          <p className="mt-2 text-3xl font-black text-white">{status.critical_blocker_count}/{status.high_blocker_count}</p>
          <p className="mt-2 text-sm text-slate-400">Must be closed before broad public traffic.</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Manual approval</p>
          <p className="mt-2 text-3xl font-black text-white">{status.manual_approval_required ? "Required" : "Set"}</p>
          <p className="mt-2 text-sm text-slate-400">Founder/admin live QA approval is never automatic.</p>
        </div>
      </div>

      <CommandNotice
        tone="warning"
        title="Public release wording guardrail"
        text={status.safe_release_wording}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {status.gates.map((gate) => <GateCard key={gate.key} gate={gate} />)}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
        <article className="glass-tile p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Claim checker</p>
              <h2 className="mt-2 text-2xl font-black text-white">Block unsafe launch copy</h2>
            </div>
            {claimResult ? <StatusPill status={claimResult.safe ? "Safe" : "Blocked"} /> : null}
          </div>
          <form onSubmit={checkClaim} className="mt-4 grid gap-3">
            <textarea
              value={claimText}
              onChange={(event) => setClaimText(event.target.value)}
              className="min-h-28 rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-white outline-none focus:border-cyan/50"
              placeholder="Paste release note, landing copy, client handoff text, or trust page wording..."
            />
            <button className="btn-primary w-fit" type="submit" disabled={checkingClaim}>
              {checkingClaim ? "Checking..." : "Check wording"}
            </button>
          </form>
          {claimResult ? (
            <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-slate-300">
              <p className="font-black text-white">{claimResult.safe ? "Safe public wording" : `Blocked claim: ${claimResult.blocked_claim}`}</p>
              {claimResult.rewrite_hint ? <p className="mt-2 text-slate-400">{claimResult.rewrite_hint}</p> : null}
            </div>
          ) : null}
        </article>

        <article className="glass-tile p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Safe missing labels</p>
          <h2 className="mt-2 text-2xl font-black text-white">No fake provider output</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {status.safe_missing_labels.map((label) => <StatusPill key={label} status={label} />)}
          </div>
          <p className="mt-5 text-sm leading-6 text-slate-400">Never collect: {status.never_collect.join(", ")}.</p>
          <ul className="mt-4 grid gap-2 text-sm text-slate-400">
            {status.not_claimed.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
      </div>

      <article className="glass-tile p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Public release checklist</p>
            <h2 className="mt-2 text-2xl font-black text-white">Manual QA before launch</h2>
          </div>
          <Link className="btn-secondary" href="/production-deployment-qa">Open deployment QA</Link>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {checklist.sections.map((section) => (
            <div key={section.area} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-black text-white">{section.area}</h3>
                <StatusPill status={section.required ? "Required" : "Optional"} />
              </div>
              <ul className="mt-4 grid gap-2 text-sm leading-6 text-slate-400">
                {section.items.map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </article>

      <article className="glass-tile p-5">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Commands</p>
        <h2 className="mt-2 text-2xl font-black text-white">Build, deploy, and verify</h2>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {Object.entries(deployPlan.commands).map(([name, commands]) => (
            <CommandBlock key={name} title={name} commands={commands} />
          ))}
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {deployPlan.live_checks.map((item) => (
            <div key={`${item.target}-${item.check}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="font-black text-white">{item.target}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{item.check}</p>
            </div>
          ))}
        </div>
      </article>

      <article className="glass-tile p-5">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Release notes</p>
        <h2 className="mt-2 text-2xl font-black text-white">{releaseNotes.title}</h2>
        <p className="mt-4 text-sm leading-7 text-slate-400">{releaseNotes.safe_intro}</p>
        <div className="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {releaseNotes.included_layers.map((layer) => (
            <p key={layer} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">{layer}</p>
          ))}
        </div>
        <CommandNotice tone="warning" title="Release gate" text={releaseNotes.release_gate} />
      </article>

      <article className="glass-tile p-5">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">What remains after Phase 30</p>
        <h2 className="mt-2 text-2xl font-black text-white">Live proof, providers, workers, legal, and pilots</h2>
        <p className="mt-3 text-sm leading-7 text-slate-400">{remaining.summary}</p>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {remaining.next_deep_workstreams.map((item) => (
            <div key={item.area} className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-black text-white">{item.area}</h3>
                <StatusPill status={item.priority} />
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-400">{item.work}</p>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
