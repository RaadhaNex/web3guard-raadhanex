"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";

const commands = [
  {
    group: "Start",
    items: [
      { label: "Unified Launch Scanner", href: "/scanner/unified-url", keywords: "scan scanner url launch evidence website dapp" },
      { label: "Scanner Hub", href: "/scanner", keywords: "all scanners modules command center" },
      { label: "Dashboard", href: "/dashboard", keywords: "projects scans reports history workspace" },
      { label: "Projects", href: "/dashboard/projects", keywords: "saved project workspace" },
    ],
  },
  {
    group: "Reports",
    items: [
      { label: "Professional Report Builder", href: "/report/professional", keywords: "pdf html markdown json export artifacts" },
      { label: "Sample Reports", href: "/sample-reports", keywords: "example report evidence wording" },
      { label: "Public Registry", href: "/registry", keywords: "public reports registry verify" },
    ],
  },
  {
    group: "Trust",
    items: [
      { label: "Methodology", href: "/methodology", keywords: "scoring score split confidence" },
      { label: "Limitations", href: "/limitations", keywords: "not certified audit boundaries" },
      { label: "Feature Status", href: "/feature-status", keywords: "integration tool not installed provider configured" },
      { label: "Engine Depth", href: "/engine-depth", keywords: "slither aderyn semgrep mythril goplus etherscan github real tools" },
      { label: "Provider Readiness", href: "/provider-readiness", keywords: "etherscan goplus github api keys provider integrations" },
      { label: "Responsible Use", href: "/responsible-use", keywords: "no exploit no private key no wallet signing" },
      { label: "Launch QA Board", href: "/launch-qa", keywords: "phase eight final ui qa mobile overflow checklist" },
    ],
  },
  {
    group: "Free tools",
    items: [
      { label: "Free Tools Console", href: "/free-tools", keywords: "checklist security txt robots sitemap bounty ci workflow" },
      { label: "Bug Bounty Readiness", href: "/bug-bounty", keywords: "immunefi bounty triage" },
      { label: "CI/CD Security", href: "/cicd", keywords: "github action workflow scanner" },
      { label: "Developer API", href: "/developer-api", keywords: "api integration key docs" },
    ],
  },
];

const flatCommands = commands.flatMap((group) => group.items.map((item) => ({ ...item, group: group.group })));

export function CommandPalette() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const isCommand = event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey);
      if (isCommand) {
        event.preventDefault();
        setOpen((value) => !value);
        return;
      }
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    setOpen(false);
    setQuery("");
  }, [pathname]);

  useEffect(() => {
    if (open) {
      const timer = window.setTimeout(() => inputRef.current?.focus(), 50);
      return () => window.clearTimeout(timer);
    }
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return flatCommands;
    return flatCommands.filter((item) => `${item.group} ${item.label} ${item.href} ${item.keywords}`.toLowerCase().includes(q));
  }, [query]);

  return (
    <>
      <button
        type="button"
        className="command-fab"
        onClick={() => setOpen(true)}
        aria-label="Open command palette"
      >
        <span className="mono">⌘K</span>
      </button>

      {open ? (
        <div className="command-overlay" role="dialog" aria-modal="true" aria-label="Command palette">
          <button className="command-backdrop" type="button" aria-label="Close command palette" onClick={() => setOpen(false)} />
          <div className="command-modal">
            <div className="command-search-row">
              <span className="mono text-cyan">⌁</span>
              <input
                ref={inputRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search scanners, reports, trust pages, tools..."
                className="command-search-input"
              />
              <button type="button" className="kbd-chip" onClick={() => setOpen(false)}>ESC</button>
            </div>

            <div className="command-status-grid">
              <span className="badge badge-green">Pre-audit only</span>
              <span className="badge badge-cyan">No wallet signing</span>
              <span className="badge badge-amber">Payments deferred</span>
              <span className="badge badge-purple">Real-only status</span>
            </div>

            <div className="command-result-list">
              {filtered.length ? (
                filtered.map((item) => (
                  <Link key={item.href} href={item.href} className="command-result">
                    <span className="command-result-icon mono">{item.group.slice(0, 2).toUpperCase()}</span>
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-black text-white">{item.label}</span>
                      <span className="block truncate text-xs text-slate-500">{item.group} · {item.href}</span>
                    </span>
                    <span className="ml-auto text-xs text-cyan">Open →</span>
                  </Link>
                ))
              ) : (
                <div className="command-empty">
                  <p className="font-black text-white">No matching page found.</p>
                  <p className="mt-1 text-sm text-slate-400">Try “scanner”, “report”, “feature status”, “free tools”, or “dashboard”.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
