"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";
import type { DashboardActivityItem, ProjectRecord, SavedReportRecord, ScanHistoryRecord } from "@/lib/types";

type Overview = {
  user_id: string;
  storage_mode: string;
  auth_mode: string;
  profile?: { email?: string | null; full_name?: string | null; plan?: string | null } | null;
  totals: Record<string, number | string | null>;
  projects: ProjectRecord[];
  recent_scans: ScanHistoryRecord[];
  recent_reports: SavedReportRecord[];
  activity: DashboardActivityItem[];
  real_only_note: string;
};

type DbStatus = {
  storage_mode_active: string;
  supabase_configured: boolean;
  supabase_service_role_configured: boolean;
  supabase_jwt_verify_enabled: boolean;
  counts: Record<string, number>;
  real_only_note: string;
};

type AuthState = {
  userId: string;
  email: string | null;
  accessToken: string;
};

export function DashboardClient() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [dbStatus, setDbStatus] = useState<DbStatus | null>(null);
  const [authState, setAuthState] = useState<AuthState | null>(null);
  const [projectName, setProjectName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const authHeaders = useMemo(() => {
    if (!authState?.accessToken) return undefined;
    return { Authorization: `Bearer ${authState.accessToken}` };
  }, [authState?.accessToken]);

  async function load() {
    setLoading(true);
    setError(null);

    try {
      if (!isSupabaseConfigured) {
        setError("Supabase frontend keys are missing. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Vercel and redeploy.");
        return;
      }

      const client = getSupabaseClient();
      if (!client) {
        setError("Supabase client could not be initialized.");
        return;
      }

      const {
        data: { session },
        error: sessionError,
      } = await client.auth.getSession();

      if (sessionError || !session?.user?.id || !session.access_token) {
        setAuthState(null);
        setError(sessionError?.message || "Real Supabase auth is configured, but no active session was found. Please login again.");
        return;
      }

      const activeAuth: AuthState = {
        userId: session.user.id,
        email: session.user.email ?? null,
        accessToken: session.access_token,
      };

      setAuthState(activeAuth);

      const headers = { Authorization: `Bearer ${activeAuth.accessToken}` };

      const [statusData, overviewData] = await Promise.all([
        apiGet<DbStatus>("/db/status", { headers }),
        apiGet<{ overview: Overview }>(`/dashboard/overview?user_id=${encodeURIComponent(activeAuth.userId)}`, { headers }),
      ]);

      setDbStatus(statusData);
      setOverview(overviewData.overview);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dashboard load failed");
    } finally {
      setLoading(false);
    }
  }

  async function createProject() {
    setError(null);
    setMessage(null);

    if (!authState?.userId || !authHeaders) {
      setError("Login is required before saving a project.");
      return;
    }

    try {
      await apiPost(
        "/projects",
        {
          user_id: authState.userId,
          name: projectName,
          website_url: null,
          chain: null,
          project_type: "Launch readiness",
        },
        { headers: authHeaders },
      );

      setMessage("Project saved as a real authenticated account record.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save project");
    }
  }

  async function logout() {
    const client = getSupabaseClient();
    await client?.auth.signOut();
    window.location.assign("/auth/login");
  }

  useEffect(() => {
    void load();
  }, []);

  const totals = overview?.totals || {};

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Real user dashboard</p>
          <h1 className="mt-2 text-4xl font-black">User dashboard + scan history</h1>
          <p className="mt-3 max-w-3xl text-slate-600">
            This dashboard shows authenticated Supabase user records only. Missing data is shown as empty or not assessed.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className="btn-secondary" href="/dashboard/projects">Projects</Link>
          <Link className="btn-secondary" href="/dashboard/scans">Scans</Link>
          <Link className="btn-secondary" href="/dashboard/workspace">Workspace</Link>
          <Link className="btn-secondary" href="/dashboard/securescore">SecureScore</Link>
          <Link className="btn-secondary" href="/dashboard/findings">Findings</Link>
          <Link className="btn-primary" href="/scanner/unified-url">Run scan</Link>
          <button className="btn-secondary" type="button" onClick={logout}>Logout</button>
        </div>
      </div>

      <section className="grid gap-4 lg:grid-cols-4">
        <Stat label="Storage" value={dbStatus?.storage_mode_active || (loading ? "loading" : "not loaded")} />
        <Stat label="Supabase" value={dbStatus ? (dbStatus.supabase_configured ? "configured" : "not configured") : "loading"} />
        <Stat label="User" value={authState?.email || authState?.userId || (loading ? "loading" : "not signed in")} />
        <Stat label="Auth mode" value={overview?.auth_mode || (authState ? "authenticated" : loading ? "loading" : "not signed in")} />
      </section>

      {loading && <p className="mt-8 text-slate-500">Loading dashboard...</p>}

      {error ? (
        <div className="mt-8 rounded-2xl border border-amber-300 bg-amber-50 p-5 text-amber-950">
          <p className="font-black">Dashboard needs a real active session.</p>
          <p className="mt-2 text-sm">{error}</p>
          <Link href="/auth/login" className="btn-primary mt-4 inline-flex">Login</Link>
        </div>
      ) : null}

      {message && <p className="mt-8 rounded-2xl border border-emerald-300 bg-emerald-50 p-4 text-emerald-900">{message}</p>}

      {overview && !error ? (
        <>
          <section className="mt-8 grid gap-4 md:grid-cols-5">
            <Stat label="Projects" value={totals.projects ?? 0} />
            <Stat label="Saved scans" value={totals.saved_scans ?? 0} />
            <Stat label="Saved reports" value={totals.saved_reports ?? 0} />
            <Stat label="Critical/high" value={totals.critical_high_findings ?? 0} />
            <Stat label="Average score" value={totals.average_score ? `${totals.average_score}/100` : "Not scored"} />
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
            <div className="card p-6">
              <h2 className="text-2xl font-black">Create project</h2>
              <p className="mt-2 text-sm text-slate-600">Save a real project record before running scans. Scanner pages can save outputs to dashboard using these same APIs.</p>
              <label className="mt-5 block text-sm font-bold text-slate-700">Project name</label>
              <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="Project name" />
              <button className="btn-secondary mt-5" onClick={createProject} type="button">Save project only</button>
            </div>

            <div className="card p-6">
              <h2 className="text-2xl font-black">Real-only note</h2>
              <p className="mt-3 text-slate-600">{overview.real_only_note}</p>
              <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                Subscription/payment records are real records only. SecureScore and finding workflows are real saved-scan records only.
              </div>
            </div>
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-3">
            <RecordList title="Projects" empty="No saved projects yet." rows={overview.projects.map((project) => ({ href: `/dashboard/projects/${project.id}`, title: project.name, meta: `${project.chain || "Chain not set"} • ${project.website_url || "No URL"}` }))} />
            <RecordList title="Recent scans" empty="No scan history yet." rows={overview.recent_scans.map((scan) => ({ href: `/dashboard/scans/${scan.id}`, title: `${scan.module} • ${scan.score ?? "—"}`, meta: `${scan.risk_label || "No risk label"} • findings ${scan.findings_count}` }))} />
            <RecordList title="Saved reports" empty="No saved reports yet." rows={overview.recent_reports.map((report) => ({ href: `/dashboard/reports/${report.id}`, title: report.title, meta: `${report.report_id} • ${report.risk_label || "No risk label"}` }))} />
          </section>
        </>
      ) : null}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 truncate text-lg font-black text-slate-950">{value}</p>
    </div>
  );
}

function RecordList({ title, empty, rows }: { title: string; empty: string; rows: Array<{ href: string; title: string; meta: string }> }) {
  return (
    <div className="card p-6">
      <h3 className="text-xl font-black">{title}</h3>
      <div className="mt-4 grid gap-3">
        {rows.length === 0 ? (
          <p className="text-sm text-slate-500">{empty}</p>
        ) : (
          rows.map((row) => (
            <Link key={row.href} href={row.href} className="rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-cyan hover:bg-cyan/10">
              <p className="font-bold text-slate-950">{row.title}</p>
              <p className="mt-1 text-xs text-slate-500">{row.meta}</p>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
