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
      { label: "Workflow Board", href: "/dashboard/workflow", keywords: "timeline risk trend scan comparison findings tasks comments" },
      { label: "Projects", href: "/dashboard/projects", keywords: "saved project workspace" },
    ],
  },
  {
    group: "Reports",
    items: [
      { label: "Professional Report Builder", href: "/report/professional", keywords: "pdf html markdown json export artifacts" },
      { label: "Report Verification", href: "/report/verify", keywords: "verify hash report integrity evidence findings workflow" },
      { label: "Public Trust Pages", href: "/trust-pages", keywords: "public trust page project readiness evidence ledger report hash disclosure" },
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
      { label: "Billing & Payment Final", href: "/billing", keywords: "razorpay upi payment billing subscription webhook plan limits" },
      { label: "Responsible Use", href: "/responsible-use", keywords: "no exploit no private key no wallet signing" },
      { label: "Launch QA Board", href: "/launch-qa", keywords: "final ui qa mobile overflow checklist" },
      { label: "Production Deployment QA", href: "/production-deployment-qa", keywords: "vercel render supabase production deployment qa security headers robots sitemap live routes" },
      { label: "EON Risk Graph", href: "/eon", keywords: "risk graph fix plan evidence ledger next best action launch blockers" },
      { label: "Launch Trust Readiness", href: "/trust-readiness", keywords: "founder trust score launch readiness score evidence completeness fixes monitoring bounty" },
      { label: "India Launch Pack", href: "/india-launch", keywords: "hindi hinglish india founder investor due diligence hackathon upi opsec launch pack" },
      { label: "Security Copilot Workspace", href: "/security-copilot", keywords: "ai coach copilot assistant next steps fix explanation commands report wording local fallback" },
      { label: "Community Review Layer", href: "/community-review", keywords: "community review request feedback triage reviewer manual safe scope" },
      { label: "Community Review Admin", href: "/community-review/admin", keywords: "admin moderation triage feedback queue reviewer requests" },
      { label: "Security Passport", href: "/security-passport", keywords: "passport trust network readiness report hash evidence monitoring community review external audit links" },
      { label: "Security Passport Admin", href: "/security-passport/admin", keywords: "admin passport trust network overview monitoring community external links" },
      { label: "Security Test Generator", href: "/security-tests", keywords: "foundry echidna slither aderyn semgrep tests properties defensive templates" },
      { label: "Sentinel Monitoring", href: "/sentinel", keywords: "monitoring vulnerability intelligence admin user alerts advisories" },
      { label: "Continuous Monitoring Lite", href: "/continuous-monitoring", keywords: "scheduled recheck stale report website drift github monitoring alerts" },
      { label: "Monitoring Admin Board", href: "/continuous-monitoring/admin", keywords: "admin monitoring due configs alerts scheduler snapshots" },
      { label: "Sentinel Intelligence", href: "/sentinel/intelligence", keywords: "nvd osv github advisory cisa kev indexed vulnerabilities risk mapping" },
      { label: "Sentinel Admin Board", href: "/sentinel/admin", keywords: "admin intelligence source health public stats disclosure queue" },
      { label: "Responsible Disclosure Draft", href: "/sentinel/disclosure", keywords: "responsible disclosure draft template contact security" },
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
              <span className="badge badge-cyan">Payment verified only</span>
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
