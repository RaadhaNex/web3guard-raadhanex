"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type JsonMap = Record<string, unknown>;
type Mode = "monitoring" | "integrations" | "worker" | "reviewers" | "delivery";

function isRecord(value: unknown): value is JsonMap {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown, fallback = "—") {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return fallback;
  }
}

function asArray(value: unknown): JsonMap[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function asRecord(value: unknown): JsonMap {
  return isRecord(value) ? value : {};
}

function jsonText(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function statusTone(value: unknown) {
  const text = asText(value, "").toLowerCase();
  if (text.includes("ready") || text.includes("approved") || text.includes("valid") || text.includes("resolved") || text.includes("accepted")) return "badge-green";
  if (text.includes("blocked") || text.includes("rejected") || text.includes("critical") || text.includes("high") || text.includes("revoked")) return "badge-red";
  if (text.includes("draft") || text.includes("pending") || text.includes("screening") || text.includes("open") || text.includes("warning")) return "badge-amber";
  return "badge-cyan";
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mt-4 max-h-[480px] overflow-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs leading-5 text-slate-300">{jsonText(value)}</pre>;
}

function MetricCard({ label, value, tone = "cyan" }: { label: string; value: unknown; tone?: "cyan" | "green" | "amber" | "red" }) {
  const toneClass = {
    cyan: "border-cyan/15 bg-cyan/5 text-cyan",
    green: "border-emerald-400/20 bg-emerald-500/10 text-emerald-100",
    amber: "border-amber-400/20 bg-amber-500/10 text-amber-100",
    red: "border-red-400/20 bg-red-500/10 text-red-100",
  }[tone];
  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <p className="text-xs font-black uppercase tracking-[0.18em] opacity-80">{label}</p>
      <p className="mt-2 text-2xl font-black text-white">{asText(value, "0")}</p>
    </div>
  );
}

function ItemTable({ title, items, columns }: { title: string; items: JsonMap[]; columns: string[] }) {
  return (
    <section className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-black text-white">{title}</h3>
        <span className="badge badge-cyan">{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="mt-4 text-sm leading-6 text-slate-400">No records yet. Create or ingest real evidence first.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
              <tr>{columns.map((column) => <th key={column} className="px-3 py-3">{column}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {items.slice(0, 12).map((item, index) => (
                <tr key={`${asText(item.id || item.event_id || item.report_id, title)}-${index}`}>
                  {columns.map((column) => {
                    const key = column.toLowerCase().replace(/\s+/g, "_");
                    const raw = item[key] ?? item[column] ?? item[column.toLowerCase()] ?? item.id;
                    return (
                      <td key={column} className="max-w-[220px] truncate px-3 py-3 text-slate-300">
                        {key === "status" ? <span className={`badge ${statusTone(raw)}`}>{asText(raw)}</span> : asText(raw)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

const modeCopy: Record<Mode, { label: string; title: string; body: string; primary: string }> = {
  monitoring: {
    label: "Phase N",
    title: "Professional monitoring dashboard",
    body: "Track post-review baselines, open drift events, acknowledged events, and continuous assurance readiness in one clean console.",
    primary: "/professional-ops/monitoring-dashboard",
  },
  integrations: {
    label: "Phase O + P",
    title: "GitHub + on-chain webhook setup",
    body: "Use real webhook/provider events as evidence for drift detection. No fake monitoring and no unsafe public claim.",
    primary: "/professional-ops/github-webhook/setup",
  },
  worker: {
    label: "Phase Q",
    title: "Foundry/Echidna isolated worker runner",
    body: "Run formal/fuzz tools only when the isolated worker is explicitly enabled. Disabled tools show Not Assessed / Provider Not Configured.",
    primary: "/professional-ops/worker/status",
  },
  reviewers: {
    label: "Phase R",
    title: "Reviewer and auditor onboarding",
    body: "Create reviewer profiles, track verification gates, and avoid certified-audit claims until real reviewer process exists.",
    primary: "/professional-ops/reviewers",
  },
  delivery: {
    label: "Phase S",
    title: "Client-facing professional report delivery",
    body: "Create hash-verified client delivery packets with safe wording and status tracking.",
    primary: "/professional-ops/deliveries",
  },
};

export function ProfessionalOpsConsoleClient({ mode }: { mode: Mode }) {
  const copy = modeCopy[mode];
  const [status, setStatus] = useState<JsonMap | null>(null);
  const [primary, setPrimary] = useState<JsonMap | null>(null);
  const [secondary, setSecondary] = useState<JsonMap | null>(null);
  const [activeResult, setActiveResult] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [reviewerName, setReviewerName] = useState("RAADHANEX reviewer");
  const [reviewerEmail, setReviewerEmail] = useState("");
  const [reviewerId, setReviewerId] = useState("");
  const [clientName, setClientName] = useState("Pilot Client");
  const [projectName, setProjectName] = useState("Demo Web3 Project");
  const [deliveryId, setDeliveryId] = useState("");
  const [workerFiles, setWorkerFiles] = useState('[{"path":"src/Test.sol","content":"pragma solidity ^0.8.20; contract Test { function check() public pure returns (bool) { return true; } }"}]');

  async function withBusy(action: () => Promise<void>) {
    setError(null);
    setLoading(true);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadAll() {
    await withBusy(async () => {
      const baseStatus = await apiGet<JsonMap>("/professional-ops/status");
      setStatus(baseStatus);
      if (mode === "integrations") {
        const github = await apiGet<JsonMap>("/professional-ops/github-webhook/setup");
        const onchain = await apiGet<JsonMap>("/professional-ops/onchain-webhook/setup");
        setPrimary(github);
        setSecondary(onchain);
        setActiveResult({ github, onchain });
        return;
      }
      const result = await apiGet<JsonMap>(copy.primary);
      setPrimary(result);
      setActiveResult(result);
    });
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  const statusCounts = useMemo(() => (isRecord(status?.counts) ? status.counts : {}), [status]);

  const counters = useMemo(() => {
    if (mode === "monitoring") return isRecord(primary?.counters) ? primary.counters : {};
    if (mode === "reviewers") return isRecord(primary?.status_counts) ? primary.status_counts : {};
    if (mode === "delivery") return isRecord(primary?.status_counts) ? primary.status_counts : {};
    return statusCounts;
  }, [mode, primary, statusCounts]);

  async function createReviewer() {
    await withBusy(async () => {
      const result = await apiPost<JsonMap>("/professional-ops/reviewers", {
        name: reviewerName,
        email: reviewerEmail || null,
        status: "invited",
        capabilities: ["solidity", "web_api", "report_qa"],
        years_experience: 1,
        quality_score: 60,
      });
      setActiveResult(result);
      const reviewer = isRecord(result.reviewer) ? result.reviewer : null;
      if (reviewer?.id) setReviewerId(asText(reviewer.id, ""));
      setPrimary(await apiGet<JsonMap>("/professional-ops/reviewers"));
    });
  }

  async function approveReviewer() {
    await withBusy(async () => {
      const result = await apiPost<JsonMap>(`/professional-ops/reviewers/${encodeURIComponent(reviewerId)}/status`, {
        status: "approved",
        identity_verified: true,
        nda_signed: true,
        conflict_check_completed: true,
        sample_review_completed: true,
        quality_score: 82,
        notes: "Approved for pre-audit readiness review workflow only. No certified-audit claim is allowed.",
      });
      setActiveResult(result);
      setPrimary(await apiGet<JsonMap>("/professional-ops/reviewers"));
    });
  }

  async function createDelivery() {
    await withBusy(async () => {
      const result = await apiPost<JsonMap>("/professional-ops/deliveries", {
        client_name: clientName,
        project_name: projectName,
        summary: "Pre-audit readiness delivery packet prepared from current Web3Guard evidence. Not a certified audit.",
        included_artifacts: ["scan_summary", "review_notes", "public_proof_reference"],
        report_payload: { report_id: "W3G-DEMO-REPORT", scope: "authorized pre-audit readiness" },
      });
      setActiveResult(result);
      const delivery = isRecord(result.delivery) ? result.delivery : null;
      if (delivery?.id) setDeliveryId(asText(delivery.id, ""));
      setPrimary(await apiGet<JsonMap>("/professional-ops/deliveries"));
    });
  }

  async function verifyDelivery() {
    await withBusy(async () => {
      const result = await apiGet<JsonMap>(`/professional-ops/deliveries/${encodeURIComponent(deliveryId)}/verify`);
      setActiveResult(result);
    });
  }

  async function runWorker() {
    await withBusy(async () => {
      let files: unknown = [];
      try {
        files = JSON.parse(workerFiles);
      } catch {
        throw new Error("Worker files JSON invalid hai.");
      }
      const result = await apiPost<JsonMap>("/professional-ops/worker/run", {
        runner: "foundry",
        files,
        authorization_confirmed: true,
        real_only_acknowledged: true,
      });
      setActiveResult(result);
      setPrimary(await apiGet<JsonMap>("/professional-ops/worker/runs"));
    });
  }

  const primaryEvents = asRecord(primary?.events);
  const monitoringRows = asArray(primaryEvents.open);
  const baselineRows = asArray(primary?.baselines);
  const reviewerRows = asArray(primary?.reviewers);
  const deliveryRows = asArray(primary?.deliveries);
  const runRows = asArray(primary?.runs);

  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-white/10 bg-white/[0.035] p-6 shadow-2xl shadow-black/20 sm:p-8">
        <p className="section-label">{copy.label}</p>
        <h1 className="mt-3 max-w-5xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">{copy.title}</h1>
        <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-400 sm:text-base">{copy.body}</p>
        <div className="mt-7 flex flex-wrap gap-3">
          <button type="button" onClick={() => void loadAll()} className="btn-primary" disabled={loading}>{loading ? "Loading..." : "Refresh"}</button>
          <Link className="btn-secondary" href="/admin/reviewer">Reviewer workbench</Link>
          <Link className="btn-secondary" href="/report/proof">Public proof</Link>
          <Link className="btn-secondary" href="/professional/monitoring">Monitoring</Link>
          <Link className="btn-secondary" href="/professional/integrations">Integrations</Link>
          <Link className="btn-secondary" href="/professional/worker">Worker</Link>
        </div>
        {error ? <div className="mt-5 rounded-2xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">{error}</div> : null}
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-4">
        <MetricCard label="Reviewers" value={statusCounts.reviewers ?? 0} />
        <MetricCard label="Deliveries" value={statusCounts.deliveries ?? 0} tone="green" />
        <MetricCard label="Worker runs" value={statusCounts.worker_runs ?? 0} tone="amber" />
        <MetricCard label="Direct claim" value="Blocked" tone="red" />
      </section>

      {Object.keys(counters).length > 0 ? (
        <section className="mt-6 grid gap-4 md:grid-cols-4">
          {Object.entries(counters).slice(0, 8).map(([key, value]) => <MetricCard key={key} label={key.replace(/_/g, " ")} value={value} />)}
        </section>
      ) : null}

      {mode === "monitoring" ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <ItemTable title="Open drift events" items={monitoringRows} columns={["id", "baseline_id", "severity", "status", "created_at"]} />
          <ItemTable title="Monitoring baselines" items={baselineRows} columns={["id", "project_name", "baseline_type", "status", "created_at"]} />
        </section>
      ) : null}

      {mode === "integrations" ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="glass-tile p-6"><h2 className="text-2xl font-black text-white">GitHub webhook</h2><JsonBlock value={primary} /></div>
          <div className="glass-tile p-6"><h2 className="text-2xl font-black text-white">On-chain/provider webhook</h2><JsonBlock value={secondary} /></div>
        </section>
      ) : null}

      {mode === "worker" ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black text-white">Safe worker request</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Default env keeps execution disabled. Run returns Provider Not Configured unless isolated execution is enabled.</p>
            <textarea value={workerFiles} onChange={(event) => setWorkerFiles(event.target.value)} className="mt-4 min-h-[180px] w-full rounded-2xl border border-white/10 bg-black/30 p-4 font-mono text-xs text-slate-200 outline-none" />
            <button type="button" className="btn-primary mt-4" onClick={() => void runWorker()} disabled={loading}>Run Foundry worker check</button>
          </div>
          <ItemTable title="Recent worker runs" items={runRows} columns={["id", "runner", "status", "files_count", "created_at"]} />
        </section>
      ) : null}

      {mode === "reviewers" ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black text-white">Reviewer onboarding</h2>
            <input value={reviewerName} onChange={(event) => setReviewerName(event.target.value)} className="mt-4 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none" placeholder="Reviewer name" />
            <input value={reviewerEmail} onChange={(event) => setReviewerEmail(event.target.value)} className="mt-3 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none" placeholder="Reviewer email" />
            <input value={reviewerId} onChange={(event) => setReviewerId(event.target.value)} className="mt-3 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none" placeholder="Reviewer ID for approval" />
            <div className="mt-4 flex flex-wrap gap-3"><button className="btn-primary" onClick={() => void createReviewer()} disabled={loading}>Create invite</button><button className="btn-secondary" onClick={() => void approveReviewer()} disabled={!reviewerId || loading}>Approve with gates</button></div>
          </div>
          <ItemTable title="Reviewer profiles" items={reviewerRows} columns={["id", "name", "role", "status", "quality_score"]} />
        </section>
      ) : null}

      {mode === "delivery" ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black text-white">Client delivery packet</h2>
            <input value={clientName} onChange={(event) => setClientName(event.target.value)} className="mt-4 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none" placeholder="Client name" />
            <input value={projectName} onChange={(event) => setProjectName(event.target.value)} className="mt-3 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none" placeholder="Project name" />
            <input value={deliveryId} onChange={(event) => setDeliveryId(event.target.value)} className="mt-3 w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none" placeholder="Delivery ID for verification" />
            <div className="mt-4 flex flex-wrap gap-3"><button className="btn-primary" onClick={() => void createDelivery()} disabled={loading}>Create delivery</button><button className="btn-secondary" onClick={() => void verifyDelivery()} disabled={!deliveryId || loading}>Verify hash</button></div>
          </div>
          <ItemTable title="Client deliveries" items={deliveryRows} columns={["id", "client_name", "project_name", "status", "created_at"]} />
        </section>
      ) : null}

      <section className="mt-8 rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-xl font-black text-white">Latest API response</h2>
          <span className="badge badge-red">No certified-audit claim</span>
        </div>
        <JsonBlock value={activeResult || status} />
      </section>
    </main>
  );
}
