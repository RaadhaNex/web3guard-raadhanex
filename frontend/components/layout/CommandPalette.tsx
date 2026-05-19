"use client";

import Link from "next/link";
import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";

const commands = [
  {
    group: "Core flow",
    items: [
      { label: "Scanner", href: "/scanner/unified-url", keywords: "start scan website dapp api contract github wallet admin" },
      { label: "Results", href: "/results", keywords: "assessed not assessed needs api key provider configured tool not installed" },
      { label: "Report", href: "/report", keywords: "pilot report export professional limitations" },
      { label: "Pricing", href: "/pricing", keywords: "999 pilot readiness report razorpay upi payment validation" },
      { label: "Docs", href: "/docs", keywords: "methodology limitations responsible use" },
    ],
  },
  {
    group: "Setup",
    items: [
      { label: "Dashboard", href: "/dashboard", keywords: "projects scans saved reports history" },
      { label: "Saved scans", href: "/dashboard/scans", keywords: "scan history saved results" },
      { label: "Payment validation", href: "/payment-validation", keywords: "razorpay test live webhook signature" },
      { label: "First 10 users", href: "/launch-pack", keywords: "first ten users outreach sample report" },
      { label: "Advanced tools", href: "/advanced", keywords: "worker provider sentinel passport metrics agency" },
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

const MAX_RESULTS = 10;

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
    return matches.slice(0, MAX_RESULTS);
  }, [deferredQuery]);

  return (
    <>
      <button type="button" className="command-fab clean-command-fab" onClick={() => setOpen(true)} aria-label="Open command palette">
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
                placeholder="Search scanner, results, report, pricing, docs..."
                className="command-search-input"
              />
              <button type="button" className="kbd-chip" onClick={() => setOpen(false)}>ESC</button>
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
                  <p className="mt-1 text-sm text-slate-400">Try scanner, results, report, pricing, or docs.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
