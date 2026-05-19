"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";

type VerificationResponse = {
  ok: boolean;
  verified?: boolean;
  reason?: string;
  public_id?: string;
  report_id?: string;
  visibility?: string;
  stored_report_hash?: string;
  submitted_report_hash?: string;
  packet?: VerificationPacket | null;
  safety_boundaries?: Record<string, unknown>;
  real_only_note?: string;
};

type VerificationPacket = {
  ok: boolean;
  version: string;
  source: string;
  report_id?: string;
  report_hash?: string;
  project_name?: string;
  risk_label?: string;
  score?: string | number | null;
  required_missing?: string[];
  verification?: {
    payload_integrity_digest?: string;
    metadata_integrity_ready?: boolean;
    scope?: string;
  };
  evidence_snapshot?: {
    assessed_modules?: string[];
    not_assessed_modules?: string[];
    evidence_summary_count?: number;
    evidence_items_count?: number;
    evidence_required_count?: number;
    evidence_required?: Array<Record<string, unknown>>;
  };
  finding_status_workflow?: {
    summary?: Record<string, number>;
    allowed_statuses?: string[];
    items?: Array<{
      id: string;
      title: string;
      module: string;
      severity: string;
      status: string;
      owner: string;
      next_action: string;
      verify: string;
    }>;
  };
  real_only_note?: string;
};

function asJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function shortHash(value?: string) {
  if (!value) return "—";
  if (value.length <= 18) return value;
  return `${value.slice(0, 10)}…${value.slice(-8)}`;
}

function StatusBadge({ verified, label }: { verified?: boolean; label?: string }) {
  if (verified === true) return <span className="badge badge-green">Verified hash match</span>;
  if (verified === false) return <span className="badge badge-red">Not verified</span>;
  return <span className="badge badge-amber">{label || "Needs input"}</span>;
}

export function ReportVerificationClient() {
  const searchParams = useSearchParams();
  const initialPublicId = searchParams.get("public_id") || searchParams.get("id") || "";
  const initialHash = searchParams.get("report_hash") || searchParams.get("hash") || "";

  const [publicId, setPublicId] = useState(initialPublicId);
  const [reportHash, setReportHash] = useState(initialHash);
  const [rawPayload, setRawPayload] = useState("");
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [packet, setPacket] = useState<VerificationPacket | null>(null);
  const [status, setStatus] = useState("Enter a public report ID + hash, or paste a report JSON payload.");
  const [busy, setBusy] = useState(false);

  const parsedPayload = useMemo(() => {
    if (!rawPayload.trim()) return null;
    try {
      const parsed = JSON.parse(rawPayload);
      return parsed.report ?? parsed;
    } catch {
      return null;
    }
  }, [rawPayload]);

  async function verifyPublic() {
    const cleanId = publicId.trim();
    const cleanHash = reportHash.trim();
    if (!cleanId || !cleanHash) {
      setStatus("Public report ID and report hash are required.");
      return;
    }
    setBusy(true);
    setStatus("Checking public report hash against the stored record...");
    try {
      const data = await apiGet<VerificationResponse>(`/report-verification/public/${encodeURIComponent(cleanId)}?report_hash=${encodeURIComponent(cleanHash)}`);
      setResult(data);
      setPacket(data.packet || null);
      setStatus(data.reason || "Verification response received.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Verification failed.");
      setResult(null);
      setPacket(null);
    } finally {
      setBusy(false);
    }
  }

  async function verifyPayload() {
    if (!parsedPayload) {
      setStatus(rawPayload.trim() ? "JSON is not valid yet." : "Paste a report JSON payload first.");
      return;
    }
    setBusy(true);
    setStatus("Building local verification packet from supplied report payload...");
    try {
      const data = await apiPost<VerificationPacket>("/report-verification/payload", { report: parsedPayload });
      setPacket(data);
      setResult(null);
      setStatus("Verification packet ready. This proves metadata shape only, not audit safety.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Payload verification failed.");
      setPacket(null);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (initialPublicId && initialHash) {
      void verifyPublic();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const evidence = packet?.evidence_snapshot;
  const workflow = packet?.finding_status_workflow;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <section className="glass-tile p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="section-label">Verify public report</p>
            <h2 className="mt-2 text-2xl font-black text-white">Report ID + hash check</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Use this to confirm that a shared report hash matches a stored public/private report record. It does not certify the project as secure.
            </p>
          </div>
          <StatusBadge verified={result?.verified} />
        </div>

        <div className="mt-5 grid gap-4">
          <label className="grid gap-2 text-sm font-semibold text-slate-300">
            Public report ID
            <input className="input" value={publicId} onChange={(event) => setPublicId(event.target.value)} placeholder="rpt_..." />
          </label>
          <label className="grid gap-2 text-sm font-semibold text-slate-300">
            Report hash
            <input className="input mono" value={reportHash} onChange={(event) => setReportHash(event.target.value)} placeholder="sha256 report hash" />
          </label>
          <button className="btn-primary" type="button" onClick={() => void verifyPublic()} disabled={busy}>
            {busy ? "Checking..." : "Verify stored report"}
          </button>
        </div>

        <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-slate-300">
          <p className="font-black text-white">What verification means</p>
          <p className="mt-2">
            A verified result means the submitted hash matches the report record stored by Web3Guard. It does not mean the project passed a certified audit, has no vulnerabilities, or is safe to launch.
          </p>
        </div>

        <div className="mt-6">
          <p className="section-label">Verify raw payload</p>
          <textarea
            className="textarea mt-3 min-h-[260px]"
            value={rawPayload}
            onChange={(event) => setRawPayload(event.target.value)}
            placeholder='Paste report JSON with "report_id" and "report_hash" to generate an evidence snapshot.'
          />
          <div className="mt-3 flex flex-wrap gap-3">
            <button className="btn-secondary" type="button" onClick={() => void verifyPayload()} disabled={busy}>Build payload packet</button>
            <button className="btn-ghost" type="button" onClick={() => setRawPayload(asJson(parsedPayload))} disabled={!parsedPayload}>Format JSON</button>
          </div>
        </div>

        <p className="mt-5 rounded-2xl border border-cyan/15 bg-cyan/10 p-4 text-sm leading-6 text-cyan-50">{status}</p>
      </section>

      <section className="grid gap-5">
        <div className="glass-tile p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="section-label">Verification packet</p>
              <h2 className="mt-2 text-2xl font-black text-white">Traceability summary</h2>
            </div>
            <StatusBadge verified={result?.verified} label={packet ? "Packet ready" : "No packet"} />
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Report ID" value={packet?.report_id || result?.report_id || "—"} />
            <Metric label="Hash" value={shortHash(packet?.report_hash || result?.stored_report_hash)} />
            <Metric label="Risk label" value={packet?.risk_label || "—"} />
            <Metric label="Score" value={packet?.score === undefined || packet?.score === null ? "—" : String(packet.score)} />
          </div>

          <div className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4 text-xs leading-6 text-slate-400">
            <p><strong className="text-white">Payload digest:</strong> {packet?.verification?.payload_integrity_digest || "—"}</p>
            <p><strong className="text-white">Scope:</strong> {packet?.verification?.scope || "metadata_integrity_only"}</p>
            <p><strong className="text-white">Missing required fields:</strong> {packet?.required_missing?.length ? packet.required_missing.join(", ") : "None detected"}</p>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          <div className="glass-tile p-5">
            <h3 className="text-xl font-black text-white">Evidence snapshot</h3>
            <div className="mt-4 grid gap-3 text-sm text-slate-300">
              <p>Assessed modules: <strong className="text-white">{evidence?.assessed_modules?.length ?? 0}</strong></p>
              <p>Not Assessed modules: <strong className="text-white">{evidence?.not_assessed_modules?.length ?? 0}</strong></p>
              <p>Evidence items: <strong className="text-white">{evidence?.evidence_items_count ?? 0}</strong></p>
              <p>Required evidence gaps: <strong className="text-white">{evidence?.evidence_required_count ?? 0}</strong></p>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {(evidence?.not_assessed_modules || []).slice(0, 10).map((item) => <span key={item} className="badge badge-amber">{item}</span>)}
            </div>
          </div>

          <div className="glass-tile p-5">
            <h3 className="text-xl font-black text-white">Finding workflow</h3>
            <div className="mt-4 grid gap-3 text-sm text-slate-300">
              {Object.entries(workflow?.summary || {}).map(([key, value]) => (
                <p key={key}>{key.replaceAll("_", " ")}: <strong className="text-white">{value}</strong></p>
              ))}
              {!workflow?.summary ? <p className="text-slate-500">No workflow generated yet.</p> : null}
            </div>
          </div>
        </div>

        <div className="glass-tile p-5 sm:p-6">
          <h3 className="text-xl font-black text-white">Finding status queue</h3>
          <div className="mt-4 grid gap-3">
            {(workflow?.items || []).slice(0, 12).map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={item.severity === "critical" ? "sev-critical" : item.severity === "high" ? "sev-high" : item.severity === "medium" ? "sev-medium" : "sev-info"}>{item.severity}</span>
                  <span className="badge badge-cyan">{item.status}</span>
                  <span className="mono text-xs text-slate-500">{item.module}</span>
                </div>
                <p className="mt-3 font-black text-white">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">{item.next_action}</p>
                <p className="mt-2 text-xs leading-5 text-slate-500">Verify: {item.verify}</p>
              </div>
            ))}
            {packet && !workflow?.items?.length ? <p className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-500">No findings were included in this report payload.</p> : null}
          </div>
        </div>

        <div className="rounded-3xl border border-amber-300/20 bg-amber-300/10 p-5 text-sm leading-6 text-amber-100">
          <p className="font-black">Pre-audit disclaimer</p>
          <p className="mt-2">{packet?.real_only_note || result?.real_only_note || "Verification is metadata integrity only. It is not a certified audit or guarantee of security."}</p>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-slab p-4">
      <p className="mono text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 truncate text-sm font-black text-white">{value}</p>
    </div>
  );
}
