"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import type { ProjectRecord } from "@/lib/types";
import { currentDashboardUser, fmtDate } from "./DashboardDataHelpers";

export function ProjectsClient() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [userId, setUserId] = useState("local-demo-user");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("My Web3 Launch");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [chain, setChain] = useState("Polygon");
  const [projectType, setProjectType] = useState("ERC20 / dApp");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      setUserId(ctx.userId);
      const data = await apiGet<{ projects: ProjectRecord[] }>(`/projects?user_id=${encodeURIComponent(ctx.userId)}&limit=100`, { headers: ctx.headers });
      setProjects(data.projects);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load projects");
    } finally {
      setLoading(false);
    }
  }

  async function createProject() {
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      await apiPost("/projects", { user_id: ctx.userId, name, website_url: websiteUrl || null, chain, project_type: projectType }, { headers: ctx.headers });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create project");
    }
  }

  useEffect(() => { void load(); }, []);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Phase 7.1 dashboard</p>
          <h1 className="mt-2 text-4xl font-black">Projects</h1>
          <p className="mt-3 max-w-3xl text-slate-400">Projects are real saved records for user <span className="text-white">{userId}</span>. No fake client/project rows are generated.</p>
        </div>
        <Link className="btn-secondary" href="/dashboard">Dashboard</Link>
      </div>

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6">
          <h2 className="text-2xl font-black">Create project</h2>
          <div className="mt-5 grid gap-4">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" />
            <input className="input" value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} placeholder="https://yourproject.com" />
            <input className="input" value={chain} onChange={(e) => setChain(e.target.value)} placeholder="Chain" />
            <input className="input" value={projectType} onChange={(e) => setProjectType(e.target.value)} placeholder="Project type" />
            <button className="btn-primary" onClick={createProject}>Save real project</button>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-2xl font-black">Saved projects</h2>
          {loading && <p className="mt-4 text-slate-400">Loading...</p>}
          {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
          {!loading && projects.length === 0 && <p className="mt-4 text-slate-500">No projects saved yet.</p>}
          <div className="mt-5 grid gap-3">
            {projects.map((project) => (
              <Link key={project.id} href={`/dashboard/projects/${project.id}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/40 hover:bg-cyan/10">
                <p className="font-black text-white">{project.name}</p>
                <p className="mt-1 text-sm text-slate-400">{project.chain || "Chain not set"} • {project.website_url || "No URL"}</p>
                <p className="mt-2 text-xs text-slate-500">Created {fmtDate(project.created_at)}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
