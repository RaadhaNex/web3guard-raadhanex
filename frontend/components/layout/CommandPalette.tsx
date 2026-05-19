"use client";

import Link from "next/link";
import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";

const commands = [
  {
    group: "Primary journey",
    items: [
      { label: "Scanner", href: "/scanner/unified-url", keywords: "start scan website dapp api contract github wallet admin" },
      { label: "Results", href: "/results", keywords: "assessed not assessed needs api key tool not installed" },
      { label: "Fix Plan", href: "/fix-plan", keywords: "fix blockers remediation eon next action" },
      { label: "Report", href: "/report", keywords: "export report professional verify public" },
      { label: "Pricing", href: "/pricing", keywords: "razorpay upi payment plan revenue validation" },
      { label: "Dashboard", href: "/dashboard", keywords: "projects scans saved reports history" },
      { label: "Docs", href: "/docs", keywords: "methodology limitations responsible use advanced setup" },
    ],
  },
  {
    group: "Launch validation",
    items: [
      { label: "Phase 31 Launch Validation", href: "/launch-validation", keywords: "slither render razorpay osv cisa dependency compression" },
      { label: "Billing & Payment Final", href: "/billing", keywords: "razorpay checkout webhook signature plan limits" },
      { label: "Launch Final QA", href: "/launch-final", keywords: "vercel render supabase razorpay release gates" },
      { label: "Feature Status", href: "/feature-status", keywords: "tool provider configured not assessed" },
    ],
  },
  {
    group: "Advanced tools",
    items: [
      { label: "All Scanners", href: "/scanner", keywords: "scanner hub modules" },
      { label: "Engine Depth", href: "/engine-depth", keywords: "slither aderyn semgrep mythril echidna" },
      { label: "Worker Execution", href: "/worker-execution", keywords: "real worker slither foundry mythril docker" },
      { label: "Provider Live", href: "/provider-live", keywords: "etherscan goplus github osv nvd cisa kev" },
      { label: "Security Tests", href: "/security-tests", keywords: "foundry echidna semgrep templates" },
      { label: "Sentinel", href: "/sentinel", keywords: "monitoring advisories intelligence" },
      { label: "Trust Metrics", href: "/trust-metrics", keywords: "advisory mapping disclosures public metrics" },
      { label: "Security Passport", href: "/security-passport", keywords: "passport trust network report hash" },
      { label: "Agency Launch", href: "/agency-launch", keywords: "client portfolio handoff white label" },
    ],
  },
];

const flatCommands = commands.flatMap((group) =>
  group.items.map((item) => ({
    ...item,
    group: group.group,
    searchText: `${group.group} ${item.label} ${item.href} ${item.keywords}`.toLowerCase(),
  }))
);

const MAX_DEFAULT_RESULTS = 12;
const MAX_SEARCH_RESULTS = 24;

export function CommandPalette() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
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
    const q = deferredQuery.trim().toLowerCase();
    const matches = q ? flatCommands.filter((item) => item.searchText.includes(q)) : flatCommands;
    return matches.slice(0, q ? MAX_SEARCH_RESULTS : MAX_DEFAULT_RESULTS);
  }, [deferredQuery]);

  const totalMatches = useMemo(() => {
    const q = deferredQuery.trim().toLowerCase();
    return q ? flatCommands.filter((item) => item.searchText.includes(q)).length : flatCommands.length;
  }, [deferredQuery]);

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
                placeholder="Search scan, results, fix plan, report, pricing, docs..."
                className="command-search-input"
              />
              <button type="button" className="kbd-chip" onClick={() => setOpen(false)}>ESC</button>
            </div>

            <div className="command-status-grid">
              <span className="badge badge-green">7-path journey</span>
              <span className="badge badge-cyan">No wallet signing</span>
              <span className="badge badge-amber">Missing tools visible</span>
              <span className="badge badge-purple">No fake output</span>
            </div>

            <div className="command-result-list">
              {filtered.length ? (
                <>
                  {filtered.map((item) => (
                    <Link key={item.href} href={item.href} className="command-result">
                      <span className="command-result-icon mono">{item.group.slice(0, 2).toUpperCase()}</span>
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-black text-white">{item.label}</span>
                        <span className="block truncate text-xs text-slate-500">{item.group} · {item.href}</span>
                      </span>
                      <span className="ml-auto text-xs text-cyan">Open →</span>
                    </Link>
                  ))}
                  {totalMatches > filtered.length ? (
                    <p className="px-2 pb-1 text-xs font-bold text-slate-500">
                      Showing {filtered.length} of {totalMatches}. Keep typing to narrow results.
                    </p>
                  ) : null}
                </>
              ) : (
                <div className="command-empty">
                  <p className="font-black text-white">No matching page found.</p>
                  <p className="mt-1 text-sm text-slate-400">Try “scanner”, “results”, “fix”, “payment”, “slither”, or “docs”.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
