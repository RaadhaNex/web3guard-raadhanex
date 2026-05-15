"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { FindingTaskRecord, OrganizationMemberRecord, WorkspaceOverview } from "@/lib/types";
import { currentDashboardUser, fmtDate } from "@/components/dashboard/DashboardDataHelpers";

export function WorkspaceDetailClient({ organizationId }: { organizationId: string }) {
  const [workspace, setWorkspace] = useState<WorkspaceOverview | null>(null);
  const [memberEmail, setMemberEmail] = useState("reviewer@example.com");
  const [memberRole, setMemberRole] = useState("reviewer");
  const [taskTitle, setTaskTitle] = useState("Review high-priority finding");
  const [taskSeverity, setTaskSeverity] = useState("high");
  const [comment, setComment] = useState("Workspace note saved from dashboard.");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      const data = await apiGet<{ workspace: WorkspaceOverview }>(`/organizations/${organizationId}?user_id=${encodeURIComponent(ctx.userId)}`, { headers: ctx.headers });
      setWorkspace(data.workspace);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load workspace");
    }
  }

  async function inviteMember() {
    setError(null);
    setMessage(null);
    try {
      const ctx = await currentDashboardUser();
      await apiPost(`/organizations/${organizationId}/members?user_id=${encodeURIComponent(ctx.userId)}`, {
        email: memberEmail,
        role: memberRole,
        status: "invited",
        note: "Manual invite record only. No email is sent in Phase 7.2.",
      }, { headers: ctx.headers });
      setMessage("Manual member invite record saved. No fake email invite was sent.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save member invite");
    }
  }

  async function createTask() {
    setError(null);
    setMessage(null);
    try {
      const ctx = await currentDashboardUser();
      await apiPost("/workspace/finding-tasks", {
        user_id: ctx.userId,
        organization_id: organizationId,
        title: taskTitle,
        module: "manual_review",
        severity: taskSeverity,
        status: "open",
        recommendation: "Assign this to a reviewer before launch.",
      }, { headers: ctx.headers });
      setMessage("Finding task saved as a real workspace record.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create task");
    }
  }

  async function updateTask(task: FindingTaskRecord, status: string) {
    setError(null);
    setMessage(null);
    try {
      const ctx = await currentDashboardUser();
      await apiPatch(`/workspace/finding-tasks/${task.id}?organization_id=${organizationId}&user_id=${encodeURIComponent(ctx.userId)}`, { status }, { headers: ctx.headers });
      setMessage("Task status updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update task");
    }
  }

  async function addComment() {
    setError(null);
    setMessage(null);
    try {
      const ctx = await currentDashboardUser();
      await apiPost("/workspace/comments", {
        user_id: ctx.userId,
        organization_id: organizationId,
        body: comment,
      }, { headers: ctx.headers });
      setMessage("Comment saved as a real workspace record.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add comment");
    }
  }

  useEffect(() => { void load(); }, [organizationId]);

  return <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
    <Link className="text-sm font-bold text-cyan" href="/dashboard/workspace">← Back to workspaces</Link>
    {error && <p className="mt-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
    {message && <p className="mt-6 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-emerald-100">{message}</p>}

    {workspace && <>
      <section className="mt-6 card p-6">
        <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Team workspace</p>
        <h1 className="mt-2 text-4xl font-black">{workspace.organization.name}</h1>
        <p className="mt-3 max-w-4xl text-slate-400">{workspace.real_only_note}</p>
        <div className="mt-6 grid gap-4 sm:grid-cols-4">
          <Stat label="Your role" value={workspace.current_user_role || "unknown"} />
          <Stat label="Members" value={workspace.totals.members ?? 0} />
          <Stat label="Open tasks" value={workspace.totals.open_tasks ?? 0} />
          <Stat label="Comments" value={workspace.totals.comments ?? 0} />
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="card p-6">
          <h2 className="text-xl font-black">Manual member invite</h2>
          <input className="input mt-4" value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} placeholder="reviewer@example.com" />
          <select className="select mt-3" value={memberRole} onChange={(e) => setMemberRole(e.target.value)}>
            <option>viewer</option><option>member</option><option>reviewer</option><option>admin</option>
          </select>
          <button className="btn-secondary mt-4" onClick={inviteMember}>Save invite record</button>
          <p className="mt-3 text-xs text-slate-500">Email sending is not connected yet, so this only saves a real manual invite record.</p>
        </div>
        <div className="card p-6">
          <h2 className="text-xl font-black">Create finding task</h2>
          <input className="input mt-4" value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} />
          <select className="select mt-3" value={taskSeverity} onChange={(e) => setTaskSeverity(e.target.value)}>
            <option>critical</option><option>high</option><option>medium</option><option>low</option><option>info</option>
          </select>
          <button className="btn-secondary mt-4" onClick={createTask}>Save task</button>
        </div>
        <div className="card p-6">
          <h2 className="text-xl font-black">Add comment</h2>
          <textarea className="textarea mt-4 min-h-[120px]" value={comment} onChange={(e) => setComment(e.target.value)} />
          <button className="btn-secondary mt-4" onClick={addComment}>Save comment</button>
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <Panel title="Members" empty="No members yet." rows={workspace.members.map((m) => ({ title: m.email || m.user_id || m.full_name || m.id, meta: `${m.role} • ${m.status}` }))} />
        <div className="card p-6">
          <h2 className="text-xl font-black">Finding tasks</h2>
          <div className="mt-4 grid gap-3">
            {workspace.finding_tasks.length === 0 ? <p className="text-sm text-slate-500">No finding tasks yet.</p> : workspace.finding_tasks.map((task) => <div key={task.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div><p className="font-bold text-white">{task.title}</p><p className="mt-1 text-xs text-slate-400">{task.severity} • {task.module} • {task.status}</p></div>
                <select className="select max-w-[180px]" value={task.status} onChange={(e) => updateTask(task, e.target.value)}>
                  <option>open</option><option>in_progress</option><option>fixed</option><option>false_positive</option><option>accepted_risk</option><option>needs_manual_review</option>
                </select>
              </div>
            </div>)}
          </div>
        </div>
        <Panel title="Comments" empty="No comments yet." rows={workspace.comments.map((c) => ({ title: c.body, meta: `${c.created_by_user_id} • ${fmtDate(c.created_at)}` }))} />
        <Panel title="Activity" empty="No activity yet." rows={workspace.activity.map((a) => ({ title: a.title, meta: `${a.type} • ${a.subtitle || ""} • ${fmtDate(a.created_at)}` }))} />
      </section>
    </>}
  </main>;
}

function Stat({ label, value }: { label: string; value: string | number }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 font-black text-white">{value}</p></div>; }
function Panel({ title, empty, rows }: { title: string; empty: string; rows: Array<{ title: string; meta: string }> }) { return <div className="card p-6"><h2 className="text-xl font-black">{title}</h2><div className="mt-4 grid gap-3">{rows.length === 0 ? <p className="text-sm text-slate-500">{empty}</p> : rows.map((row, i) => <div key={`${row.title}-${i}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="font-bold text-white">{row.title}</p><p className="mt-1 text-xs text-slate-400">{row.meta}</p></div>)}</div></div>; }
