"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type AdminLink = {
  label: string;
  href: string;
  description: string;
  tag: "Admin" | "Monitoring" | "Worker" | "QA" | "Revenue" | "Review" | "Provider";
};

type AdminGroup = {
  title: string;
  note: string;
  items: AdminLink[];
};

const groups: AdminGroup[] = [
  {
    title: "Revenue and lead operations",
    note: "For RAADHANEX admins only. Backend endpoints still require ADMIN_TOKEN.",
    items: [
      {
        label: "Leads dashboard",
        href: "/admin/leads",
        description: "Track lead capture, UPI references, review status, reviewer assignment, and CSV export.",
        tag: "Revenue",
      },
      {
        label: "Payments dashboard",
        href: "/admin/payments",
        description: "Manual payment verification, subscriptions, revenue summary, and status updates.",
        tag: "Revenue",
      },
      {
        label: "Super admin",
        href: "/admin/super",
        description: "Admin-level operational controls and production guardrails.",
        tag: "Admin",
      },
    ],
  },
  {
    title: "Monitoring and review operations",
    note: "Internal workflows that should not sit inside the public More menu.",
    items: [
      {
        label: "Continuous monitoring admin",
        href: "/continuous-monitoring/admin",
        description: "Operate monitoring records, alerts, and reviewer follow-up flows.",
        tag: "Monitoring",
      },
      {
        label: "Sentinel admin",
        href: "/sentinel/admin",
        description: "Manage disclosure, intelligence, and project sentinel operations.",
        tag: "Monitoring",
      },
      {
        label: "Security passport admin",
        href: "/security-passport/admin",
        description: "Review and maintain passport-style trust and security evidence records.",
        tag: "Review",
      },
      {
        label: "Community review admin",
        href: "/community-review/admin",
        description: "Handle community findings, reviewer decisions, and moderation actions.",
        tag: "Review",
      },
      {
        label: "Manual expert review",
        href: "/manual-review",
        description: "Triage findings, notes, report decisions, false positives, and accepted-risk states.",
        tag: "Review",
      },
    ],
  },
  {
    title: "Scanner worker and provider ops",
    note: "Use these when verifying Slither, Semgrep, Aderyn, provider keys, workers, and scan truth states.",
    items: [
      {
        label: "Worker execution",
        href: "/worker-execution",
        description: "Check static tool execution matrix, binary paths, and run/skip states.",
        tag: "Worker",
      },
      {
        label: "Worker runs",
        href: "/worker-runs",
        description: "Inspect recent worker executions and tool outcome history.",
        tag: "Worker",
      },
      {
        label: "Provider live",
        href: "/provider-live",
        description: "Explorer, GitHub, OSV, advisory, AI, and external provider readiness.",
        tag: "Provider",
      },
      {
        label: "Provider readiness",
        href: "/provider-readiness",
        description: "Production configuration states for APIs, keys, and optional services.",
        tag: "Provider",
      },
      {
        label: "Static artifact bridge",
        href: "/static-artifact-bridge",
        description: "Parse real Slither/Semgrep/Aderyn JSON artifacts without fake execution claims.",
        tag: "Worker",
      },
    ],
  },
  {
    title: "Internal scanner QA and advanced engines",
    note: "These are product/admin verification screens, not normal public navigation items.",
    items: [
      {
        label: "Scanner truth validation",
        href: "/scanner-truth-validation",
        description: "Validate evidence mapping, not-assessed states, and fake-claim blockers.",
        tag: "QA",
      },
      {
        label: "Scanner correlation",
        href: "/scanner-correlation",
        description: "Review correlation, P0/P1/P2/P3 prioritization, and attack-path hints.",
        tag: "QA",
      },
      {
        label: "Deep evidence accuracy",
        href: "/deep-evidence",
        description: "HAR/API capture, authorized observations, fuzz/invariant evidence, and accuracy feedback.",
        tag: "QA",
      },
      {
        label: "Detection expansion",
        href: "/detection-expansion",
        description: "Crawler, JS/API discovery, wallet/API/business/DeFi evidence, and false-positive learning.",
        tag: "QA",
      },
      {
        label: "Accuracy hardening",
        href: "/accuracy-hardening",
        description: "Benchmarking, false-positive tuning, formal/fuzz artifacts, API harness, and trust proof.",
        tag: "QA",
      },
      {
        label: "Admin governance",
        href: "/admin-pentest",
        description: "Scope, authorization, admin, role, and governance readiness workflow.",
        tag: "Admin",
      },
    ],
  },
];

function Tag({ value }: { value: AdminLink["tag"] }) {
  const tone = {
    Admin: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
    Monitoring: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
    Worker: "border-violet-300/30 bg-violet-300/10 text-violet-100",
    QA: "border-amber-300/30 bg-amber-300/10 text-amber-100",
    Revenue: "border-blue-300/30 bg-blue-300/10 text-blue-100",
    Review: "border-fuchsia-300/30 bg-fuchsia-300/10 text-fuchsia-100",
    Provider: "border-slate-300/25 bg-slate-300/10 text-slate-100",
  }[value];

  return <span className={`rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.14em] ${tone}`}>{value}</span>;
}

export function AdminOpsHub() {
  const [token, setToken] = useState("");
  const [unlocked, setUnlocked] = useState(false);

  useEffect(() => {
    const saved = window.sessionStorage.getItem("w3g_admin_session_unlocked");
    if (saved === "true") setUnlocked(true);
  }, []);

  const totalTools = useMemo(() => groups.reduce((total, group) => total + group.items.length, 0), []);

  function unlock() {
    if (!token.trim()) return;
    window.sessionStorage.setItem("w3g_admin_session_unlocked", "true");
    setUnlocked(true);
  }

  function lock() {
    window.sessionStorage.removeItem("w3g_admin_session_unlocked");
    setToken("");
    setUnlocked(false);
  }

  if (!unlocked) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
        <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/80 p-6 shadow-2xl shadow-cyan-950/20 sm:p-8">
          <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-200/80">Admin OS</p>
          <h1 className="mt-4 text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">Separated admin workspace.</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
            Admin, monitoring, worker, provider, QA, and revenue screens are no longer mixed with the public user menu. Enter your admin token locally to open the admin link hub. Backend actions still require the real ADMIN_TOKEN on each admin endpoint.
          </p>
          <div className="mt-7 rounded-3xl border border-white/10 bg-white/[0.035] p-4 sm:p-5">
            <label className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">Admin token</label>
            <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_auto]">
              <input
                type="password"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder="Paste ADMIN_TOKEN to unlock local admin navigation"
                className="input"
                onKeyDown={(event) => {
                  if (event.key === "Enter") unlock();
                }}
              />
              <button type="button" onClick={unlock} disabled={!token.trim()} className="btn-primary">
                Unlock admin hub →
              </button>
            </div>
            <p className="mt-3 text-xs leading-6 text-slate-500">
              This gate is for UI separation only. It does not expose secrets and does not replace backend token checks.
            </p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/80 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-200/80">Admin OS</p>
            <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">Admin, monitoring and ops tools.</h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
              This hub is intentionally separated from the public More menu. Use it for internal RAADHANEX operations, scanner verification, monitoring, payments, workers, and reviewer workflows.
            </p>
          </div>
          <div className="grid gap-2 rounded-3xl border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-300">
            <b className="text-white">{totalTools} admin tools grouped</b>
            <span>Backend admin actions still need ADMIN_TOKEN.</span>
            <button type="button" onClick={lock} className="rounded-xl border border-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.16em] text-slate-300 transition hover:border-red-300/40 hover:text-red-100">
              Lock admin hub
            </button>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 xl:grid-cols-2">
        {groups.map((group) => (
          <article key={group.title} className="rounded-[1.7rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
            <h2 className="text-2xl font-black text-white">{group.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{group.note}</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {group.items.map((item) => (
                <Link key={item.href} href={item.href} className="rounded-2xl border border-white/10 bg-slate-950/45 p-4 transition hover:border-cyan-300/30 hover:bg-cyan-300/[0.05]">
                  <div className="flex items-start justify-between gap-3">
                    <b className="block text-white">{item.label}</b>
                    <Tag value={item.tag} />
                  </div>
                  <small className="mt-2 block text-sm leading-6 text-slate-400">{item.description}</small>
                  <span className="mt-3 block text-xs font-black uppercase tracking-[0.16em] text-cyan-200">Open →</span>
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
