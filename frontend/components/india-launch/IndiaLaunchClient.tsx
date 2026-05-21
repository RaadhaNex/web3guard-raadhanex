"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";

type Mode = "english" | "hinglish" | "hindi";

type ChecklistItem = {
  title: string;
  description?: string;
  status?: string;
};

type IndiaLaunchPack = {
  ok: boolean;
  generated_at: string;
  mode: Mode;
  project: {
    id?: string | null;
    name: string;
    website_url?: string | null;
    chain?: string | null;
    project_type?: string | null;
  };
  readiness: { score: number; label: string; note: string };
  founder_checklist: ChecklistItem[];
  investor_summary: {
    title: string;
    one_liner: string;
    safe_disclaimer: string;
    evidence_counts: { stored_scans: number; stored_reports: number };
    recommended_investor_questions: string[];
  };
  hackathon_pack: ChecklistItem[];
  founder_opsec: ChecklistItem[];
  public_trust_summary: { headline: string; summary: string; disclaimer: string };
  payment_security_wording: Array<{ title: string; copy: string }>;
  priority_actions: Array<{ title: string; reason: string }>;
  safe_share_copy: string;
  blocked_wording: string[];
  note: string;
};

const exampleUserId = "demo-user";
const modes: Array<{ id: Mode; label: string; helper: string }> = [
  { id: "hinglish", label: "Hinglish", helper: "Best for Indian founders and hackathon teams." },
  { id: "english", label: "English", helper: "Best for investors and public reports." },
  { id: "hindi", label: "Hindi", helper: "Plain Hindi founder guidance." },
];

function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function packToMarkdown(pack: IndiaLaunchPack) {
  const lines: string[] = [];
  lines.push(`# India Launch Pack — ${pack.project.name}`);
  lines.push("");
  lines.push(`Generated: ${pack.generated_at}`);
  lines.push(`Mode: ${pack.mode}`);
  lines.push(`Launch Trust Readiness: ${pack.readiness.score}/100 (${pack.readiness.label})`);
  lines.push("");
  lines.push(`> ${pack.note}`);
  lines.push("");
  lines.push("## Safe share copy");
  lines.push(pack.safe_share_copy);
  lines.push("");
  lines.push("## Investor summary");
  lines.push(pack.investor_summary.one_liner);
  lines.push(pack.investor_summary.safe_disclaimer);
  lines.push("");
  lines.push("## Founder checklist");
  pack.founder_checklist.forEach((item) => lines.push(`- **${item.title}** — ${item.description || ""}`));
  lines.push("");
  lines.push("## Founder/Admin OpSec");
  pack.founder_opsec.forEach((item) => lines.push(`- **${item.title}** — ${item.description || ""}`));
  lines.push("");
  lines.push("## Hackathon pack");
  pack.hackathon_pack.forEach((item) => lines.push(`- **${item.title}** — ${item.description || ""}`));
  lines.push("");
  lines.push("## Priority actions");
  pack.priority_actions.forEach((item) => lines.push(`- **${item.title}** — ${item.reason}`));
  lines.push("");
  lines.push("## Blocked wording");
  pack.blocked_wording.forEach((item) => lines.push(`- ${item}`));
  return lines.join("\n");
}

function Card({ title, children, badge }: { title: string; children: React.ReactNode; badge?: string }) {
  return (
    <section className="glass-tile p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-xl font-black text-white">{title}</h2>
        {badge ? <span className="badge badge-cyan">{badge}</span> : null}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function ListItems({ items }: { items: ChecklistItem[] }) {
  return (
    <div className="grid gap-3">
      {items.map((item, index) => (
        <div key={`${item.title}-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <p className="font-black text-white">{item.title}</p>
            {item.status ? <span className="badge badge-amber">{item.status}</span> : null}
          </div>
          {item.description ? <p className="mt-2 text-sm leading-6 text-slate-400">{item.description}</p> : null}
        </div>
      ))}
    </div>
  );
}

export function IndiaLaunchClient() {
  const [userId, setUserId] = useState(exampleUserId);
  const [projectId, setProjectId] = useState("");
  const [mode, setMode] = useState<Mode>("hinglish");
  const [pack, setPack] = useState<IndiaLaunchPack | null>(null);
  const [status, setStatus] = useState("Enter user_id and generate the India launch pack from stored readiness evidence.");
  const [loading, setLoading] = useState(false);

  const markdown = useMemo(() => (pack ? packToMarkdown(pack) : ""), [pack]);

  async function loadPack() {
    const cleanUserId = userId.trim();
    if (!cleanUserId) {
      setStatus("user_id is required. Use the authenticated dashboard user ID or a local test user ID.");
      return;
    }
    setLoading(true);
    setStatus("Building India Launch Pack from stored Web3Guard evidence...");
    try {
      const query = new URLSearchParams({ user_id: cleanUserId, mode });
      if (projectId.trim()) query.set("project_id", projectId.trim());
      const data = await apiGet<IndiaLaunchPack>(`/india-launch/pack?${query.toString()}`);
      setPack(data);
      setStatus("India Launch Pack ready. Review wording before sharing publicly.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not build India Launch Pack.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink text-white">
      <section className="relative border-b border-white/10">
        <div className="pointer-events-none absolute inset-0 w3g-cyber-grid opacity-70" />
        <div className="pointer-events-none absolute left-[-10rem] top-[-12rem] h-[32rem] w-[32rem] rounded-full bg-cyan/10 blur-3xl" />
        <div className="pointer-events-none absolute right-[-10rem] top-[-8rem] h-[28rem] w-[28rem] rounded-full bg-purple-500/10 blur-3xl" />
        <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan/20 bg-cyan/[0.06] px-3.5 py-1.5 backdrop-blur-xl">
            <span className="pulse-dot h-2 w-2 rounded-full bg-cyan" />
            <span className="text-xs font-black uppercase tracking-[0.22em] text-cyan">India Launch Pack</span>
          </div>
          <h1 className="mt-5 max-w-5xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
            Founder-friendly security launch pack for Indian Web3 teams.
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-8 text-slate-300">
            Generate Hindi/Hinglish founder guidance, investor due-diligence copy, hackathon safety packs, UPI/payment wording, and public trust summaries from stored Web3Guard readiness evidence.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="badge badge-green">India-first founder UX</span>
            <span className="badge badge-cyan">Pre-audit readiness only</span>
            <span className="badge badge-amber">No audit badge claim</span>
            <span className="badge badge-purple">Hindi / Hinglish / English</span>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:px-8">
        <Card title="Generate pack" badge="Evidence-based">
          <div className="grid gap-4">
            <label className="grid gap-2 text-sm font-bold text-slate-300">
              User ID
              <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="authenticated user_id" />
            </label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">
              Project ID optional
              <input className="input" value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="project_id for one project pack" />
            </label>
            <div>
              <p className="mb-2 text-sm font-bold text-slate-300">Language mode</p>
              <div className="grid gap-3 sm:grid-cols-3">
                {modes.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setMode(item.id)}
                    className={`rounded-2xl border p-4 text-left transition ${mode === item.id ? "border-cyan/40 bg-cyan/10" : "border-white/10 bg-white/[0.03] hover:border-cyan/25"}`}
                  >
                    <p className="font-black text-white">{item.label}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{item.helper}</p>
                  </button>
                ))}
              </div>
            </div>
            <button className="btn-primary" onClick={loadPack} disabled={loading} type="button">
              {loading ? "Building..." : "Generate India Launch Pack"}
            </button>
            <p className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-slate-300">{status}</p>
            {pack ? (
              <button className="btn-secondary" type="button" onClick={() => downloadText(`india-launch-pack-${pack.project.id || "project"}.md`, markdown)}>
                Download Markdown pack
              </button>
            ) : null}
          </div>
        </Card>

        <Card title="Safe share preview" badge={pack ? `${pack.readiness.score}/100` : "Waiting"}>
          {pack ? (
            <div>
              <div className="rounded-3xl border border-cyan/20 bg-cyan/[0.06] p-5">
                <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">{pack.project.name}</p>
                <h2 className="mt-2 text-2xl font-black text-white">{pack.public_trust_summary.headline}</h2>
                <p className="mt-3 text-sm leading-7 text-slate-300">{pack.public_trust_summary.summary}</p>
                <p className="mt-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm text-amber-100">{pack.public_trust_summary.disclaimer}</p>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div className="stat-slab p-4"><p className="text-xs text-slate-500">Score type</p><p className="mt-1 font-black text-white">Readiness only</p></div>
                <div className="stat-slab p-4"><p className="text-xs text-slate-500">Scans</p><p className="mt-1 font-black text-white">{pack.investor_summary.evidence_counts.stored_scans}</p></div>
                <div className="stat-slab p-4"><p className="text-xs text-slate-500">Reports</p><p className="mt-1 font-black text-white">{pack.investor_summary.evidence_counts.stored_reports}</p></div>
              </div>
            </div>
          ) : (
            <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 text-center">
              <p className="font-black text-white">No pack generated yet.</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">Generate from stored scans/reports/trust-readiness data. Empty records will stay honest instead of showing fake proof.</p>
            </div>
          )}
        </Card>
      </section>

      {pack ? (
        <section className="mx-auto grid max-w-7xl gap-6 px-4 pb-12 sm:px-6 lg:grid-cols-2 lg:px-8">
          <Card title="Founder launch checklist" badge={pack.mode}><ListItems items={pack.founder_checklist} /></Card>
          <Card title={pack.investor_summary.title} badge="Investor-ready copy">
            <p className="text-sm leading-7 text-slate-300">{pack.investor_summary.one_liner}</p>
            <p className="mt-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm text-amber-100">{pack.investor_summary.safe_disclaimer}</p>
            <div className="mt-4 grid gap-2">
              {pack.investor_summary.recommended_investor_questions.map((question) => (
                <p key={question} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">{question}</p>
              ))}
            </div>
          </Card>
          <Card title="Hackathon demo pack" badge="Safe demo"><ListItems items={pack.hackathon_pack} /></Card>
          <Card title="Founder/Admin OpSec" badge="Hindi/Hinglish"><ListItems items={pack.founder_opsec} /></Card>
          <Card title="Payment + security wording" badge="UPI/Razorpay safe">
            <div className="grid gap-3">
              {pack.payment_security_wording.map((item) => (
                <div key={item.title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="font-black text-white">{item.title}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{item.copy}</p>
                </div>
              ))}
            </div>
          </Card>
          <Card title="Blocked public wording" badge="Do not use">
            <div className="flex flex-wrap gap-2">
              {pack.blocked_wording.map((item) => <span key={item} className="badge badge-red">{item}</span>)}
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-400">{pack.note}</p>
          </Card>
          <div className="lg:col-span-2">
            <Card title="Priority actions" badge="Next steps">
              <div className="grid gap-3 sm:grid-cols-2">
                {pack.priority_actions.map((item) => (
                  <div key={item.title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="font-black text-white">{item.title}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{item.reason}</p>
                  </div>
                ))}
              </div>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/trust-readiness" className="btn-secondary">Open trust readiness</Link>
                <Link href="/trust-pages" className="btn-secondary">Open public trust pages</Link>
                <Link href="/continuous-monitoring" className="btn-secondary">Open monitoring</Link>
              </div>
            </Card>
          </div>
        </section>
      ) : null}
    </main>
  );
}
