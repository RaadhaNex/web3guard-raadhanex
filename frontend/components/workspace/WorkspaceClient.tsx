"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { OrganizationRecord } from "@/lib/types";

type WorkspaceStatus = {
  phase: string;
  storage_mode: string;
  tables_ready: string[];
  real_only_note: string;
  local_counts: Record<string, number>;
  not_connected_yet: string[];
};

export function WorkspaceClient() {
  const [organizations, setOrganizations] = useState<OrganizationRecord[]>([]);
  const [status, setStatus] = useState<WorkspaceStatus | null>(null);
  const [name, setName] = useState("RAADHANEX Client Workspace");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [billingEmail, setBillingEmail] = useState("");
  const [notes, setNotes] = useState("Manual pre-audit review workspace.");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const authHeaders = useMemo(() => async () => {
    const token = await getSessionToken();
    return token ? { Authorization: `Bearer ${token}` } : undefined;
  }, []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const userId = await getCurrentUserId();
      const headers = await authHeaders();
      const [statusData, orgData] = await Promise.all([
        apiGet<WorkspaceStatus>("/workspace/status", { headers }),
        apiGet<{ organizations: OrganizationRecord[] }>(`/organizations?user_id=${encodeURIComponent(userId)}`, { headers }),
      ]);
      setStatus(statusData);
      setOrganizations(orgData.organizations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load workspaces");
    } finally {
      setLoading(false);
    }
  }

  async function createWorkspace() {
    setError(null);
    setMessage(null);
    try {
      const userId = await getCurrentUserId();
      const headers = await authHeaders();
      await apiPost("/organizations", {
        user_id: userId,
        name,
        website_url: websiteUrl || null,
        billing_email: billingEmail || null,
        notes,
      }, { headers });
      setMessage("Workspace saved as a real organization record. No fake team members or fake activity were created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create workspace");
    }
  }

  useEffect(() => { void load(); }, []);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Phase 7.2 workspace</p>
          <h1 className="mt-2 text-4xl font-black">Organization + team workspace</h1>
          <p className="mt-3 max-w-3xl text-slate-400">Create real client/team workspaces, invite manual reviewer records, assign findings, and track comments. Email invite sending and paid seat billing are not faked.</p>
        </div>
        <Link className="btn-secondary" href="/dashboard">Dashboard</Link>
      </div>

      {error && <p className="mb-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
      {message && <p className="mb-6 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-emerald-100">{message}</p>}

      <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="card p-6">
          <h2 className="text-2xl font-black">Create workspace</h2>
          <label className="mt-4 block text-sm font-bold text-slate-300">Organization name</label>
          <input className="input mt-2" value={name} onChange={(e) => setName(e.target.value)} />
          <label className="mt-4 block text-sm font-bold text-slate-300">Website URL</label>
          <input className="input mt-2" value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} placeholder="https://client-project.com" />
          <label className="mt-4 block text-sm font-bold text-slate-300">Billing email</label>
          <input className="input mt-2" value={billingEmail} onChange={(e) => setBillingEmail(e.target.value)} placeholder="billing@example.com" />
          <label className="mt-4 block text-sm font-bold text-slate-300">Notes</label>
          <textarea className="textarea mt-2 min-h-[100px]" value={notes} onChange={(e) => setNotes(e.target.value)} />
          <button className="btn-primary mt-5" onClick={createWorkspace}>Save real workspace</button>
        </div>

        <div className="card p-6">
          <h2 className="text-2xl font-black">Real-only workspace status</h2>
          {status && <>
            <p className="mt-3 text-slate-300">{status.real_only_note}</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {Object.entries(status.local_counts).map(([key, value]) => <Stat key={key} label={key.replaceAll("_", " ")} value={value} />)}
            </div>
            <p className="mt-5 text-sm text-slate-500">Not connected yet: {status.not_connected_yet.join(", ")}.</p>
          </>}
        </div>
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        {loading && <p className="text-slate-400">Loading workspaces...</p>}
        {organizations.map((org) => (
          <Link key={org.id} href={`/dashboard/workspace/${org.id}`} className="card p-5 transition hover:border-cyan/40">
            <p className="text-xs font-bold uppercase tracking-wide text-cyan">{org.plan || "free"} workspace</p>
            <h2 className="mt-2 text-2xl font-black">{org.name}</h2>
            <p className="mt-2 text-sm text-slate-400">{org.website_url || "No website set"}</p>
            <p className="mt-2 text-xs text-slate-500">Owner: {org.owner_user_id}</p>
          </Link>
        ))}
        {!loading && organizations.length === 0 && <p className="text-slate-500">No workspaces saved yet.</p>}
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 font-black text-white">{value}</p></div>;
}
