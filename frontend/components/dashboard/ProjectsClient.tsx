"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import type { ProjectRecord } from "@/lib/types";
import { currentDashboardUser, fmtDate } from "./DashboardDataHelpers";

export function ProjectsClient() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [userId, setUserId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [chain, setChain] = useState("");
  const [projectType, setProjectType] = useState("");

  async function load() {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const ctx = await currentDashboardUser();
      const currentUserId = ctx.userId;

      setUserId(currentUserId);

      const data = await apiGet<{ projects: ProjectRecord[] }>(
        `/projects?user_id=${encodeURIComponent(currentUserId)}`,
        {
          headers: ctx.headers,
        }
      );

      setProjects(data.projects);
    } catch (err) {
      setUserId("");
      setProjects([]);
      setError(err instanceof Error ? err.message : "Could not load projects");
    } finally {
      setLoading(false);
    }
  }

  async function createProject() {
    setError(null);
    setMessage(null);

    const cleanName = name.trim();
    const cleanWebsiteUrl = websiteUrl.trim();
    const cleanChain = chain.trim();
    const cleanProjectType = projectType.trim();

    if (!cleanName) {
      setError("Please enter a project name.");
      return;
    }

    setSaving(true);

    try {
      const ctx = await currentDashboardUser();
      const currentUserId = ctx.userId;

      await apiPost(
        "/projects",
        {
          user_id: currentUserId,
          name: cleanName,
          website_url: cleanWebsiteUrl || null,
          chain: cleanChain || null,
          project_type: cleanProjectType || null,
        },
        {
          headers: ctx.headers,
        }
      );

      setMessage("Project saved successfully.");
      setName("");
      setWebsiteUrl("");
      setChain("");
      setProjectType("");

      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create project");
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">
            Real project workspace
          </p>

          <h1 className="mt-2 text-4xl font-black">Projects</h1>

          <p className="mt-3 max-w-3xl text-slate-400">
            Projects are saved to your authenticated Web3Guard account. No demo
            project rows are generated.
          </p>

          {userId ? (
            <p className="mt-2 break-all text-xs text-slate-500">
              Account ID: <span className="text-slate-300">{userId}</span>
            </p>
          ) : null}
        </div>

        <Link className="btn-secondary" href="/dashboard">
          Dashboard
        </Link>
      </div>

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6">
          <h2 className="text-2xl font-black">Create project</h2>

          <p className="mt-2 text-sm leading-6 text-slate-400">
            Save a real project record for scan history, reports, and launch
            readiness tracking.
          </p>

          <div className="mt-5 grid gap-4">
            <input
              className="input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Project name"
            />

            <input
              className="input"
              value={websiteUrl}
              onChange={(event) => setWebsiteUrl(event.target.value)}
              placeholder="https://yourproject.com"
            />

            <input
              className="input"
              value={chain}
              onChange={(event) => setChain(event.target.value)}
              placeholder="Chain, for example Ethereum, Polygon, Base"
            />

            <input
              className="input"
              value={projectType}
              onChange={(event) => setProjectType(event.target.value)}
              placeholder="Project type, for example dApp, ERC20, NFT, DAO"
            />

            <button
              className="btn-primary"
              onClick={createProject}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save real project"}
            </button>

            {message ? (
              <p className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                {message}
              </p>
            ) : null}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-2xl font-black">Saved projects</h2>

          {loading ? (
            <p className="mt-4 text-slate-400">Loading projects...</p>
          ) : null}

          {error ? (
            <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">
              {error}
            </p>
          ) : null}

          {!loading && !error && projects.length === 0 ? (
            <p className="mt-4 text-slate-500">
              No projects saved yet. Create your first project to start tracking
              real scan history and reports.
            </p>
          ) : null}

          <div className="mt-5 grid gap-3">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/dashboard/projects/${project.id}`}
                className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/40 hover:bg-cyan/10"
              >
                <p className="font-black text-white">{project.name}</p>

                <p className="mt-1 text-sm text-slate-400">
                  {project.chain || "Chain not set"} •{" "}
                  {project.website_url || "No URL"}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  Created {fmtDate(project.created_at)}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}