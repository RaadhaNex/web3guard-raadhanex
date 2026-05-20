"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthSessionButton } from "@/components/auth/AuthSessionButton";
import KavachWingNavLogo from "@/components/brand/KavachWingNavLogo";

type NavIconName = "home" | "scan" | "price" | "more" | "result" | "report" | "docs" | "dashboard" | "saved" | "risk" | "status" | "advanced" | "payment";

type NavItem = {
  href: string;
  label: string;
  icon: NavIconName;
  activePrefixes?: string[];
};

type MoreItem = {
  href: string;
  label: string;
  description: string;
  icon: NavIconName;
  status?: "core" | "beta" | "setup";
  activePrefixes?: string[];
};

type MoreGroup = {
  title: string;
  helper: string;
  items: MoreItem[];
};

const primaryLinks: NavItem[] = [
  { href: "/", label: "Home", icon: "home" },
  { href: "/scanner/unified-url", label: "Scan", icon: "scan", activePrefixes: ["/scanner"] },
  { href: "/pricing", label: "Price", icon: "price" },
];

const moreGroups: MoreGroup[] = [
  {
    title: "Work output",
    helper: "What users need after scanning.",
    items: [
      {
        href: "/results",
        label: "Results",
        description: "See assessed modules, missing evidence, and action states.",
        icon: "result",
        status: "core",
      },
      {
        href: "/report",
        label: "Report center",
        description: "Turn scan evidence into a founder-ready readiness report.",
        icon: "report",
        status: "core",
      },
      {
        href: "/dashboard/scans",
        label: "Saved scans",
        description: "Open previous scans when login and storage are configured.",
        icon: "saved",
        status: "beta",
        activePrefixes: ["/dashboard/scans"],
      },
    ],
  },
  {
    title: "Trust and help",
    helper: "Simple pages that explain how to use Web3Guard safely.",
    items: [
      {
        href: "/docs",
        label: "Docs",
        description: "Methodology, limitations, responsible use, and setup guides.",
        icon: "docs",
        status: "core",
      },
      {
        href: "/feature-status",
        label: "Feature status",
        description: "Live, beta, manual, and not-configured feature states.",
        icon: "status",
        status: "beta",
      },
      {
        href: "/dashboard",
        label: "Dashboard",
        description: "Account workspace for saved projects and reports.",
        icon: "dashboard",
        status: "beta",
        activePrefixes: ["/dashboard"],
      },
    ],
  },
  {
    title: "Scanner intelligence",
    helper: "Advanced engines without making the header crowded.",
    items: [
      {
        href: "/risk-intelligence",
        label: "Risk intelligence",
        description: "Explain impact, future risk, fix path, and verification steps.",
        icon: "risk",
        status: "beta",
      },
      {
        href: "/scanner-correlation",
        label: "Scanner correlation",
        description: "Prioritize real findings into P0/P1/P2/P3 and attack-path hints.",
        icon: "risk",
        status: "beta",
      },
      {
        href: "/openzeppelin-pattern",
        label: "OpenZeppelin patterns",
        description: "Check Solidity evidence against OpenZeppelin-style secure patterns.",
        icon: "advanced",
        status: "beta",
      },
      {
        href: "/web-dast",
        label: "Authorized Web DAST",
        description: "Safe authorized baseline checks with no exploit automation.",
        icon: "status",
        status: "beta",
      },
      {
        href: "/admin-pentest",
        label: "Admin governance",
        description: "Scope, permission, admin, role, and governance readiness workflow.",
        icon: "advanced",
        status: "setup",
      },
    ],
  },
  {
    title: "Advanced setup",
    helper: "Keep power tools out of the main path.",
    items: [
      {
        href: "/more",
        label: "More hub",
        description: "Grouped docs, output pages, scanner surfaces, providers, workers, and setup tools.",
        icon: "advanced",
        status: "setup",
        activePrefixes: ["/more", "/advanced"],
      },
      {
        href: "/payment-validation",
        label: "Payment validation",
        description: "Razorpay/UPI verification checks for the ₹999 pilot path.",
        icon: "payment",
        status: "setup",
      },
      {
        href: "/provider-live",
        label: "Provider live",
        description: "Check configured external provider/API/tool readiness states.",
        icon: "status",
        status: "setup",
      },
    ],
  },
];

const moreLinks = moreGroups.flatMap((group) => group.items);

function isActive(pathname: string, item: { href: string; activePrefixes?: readonly string[] }) {
  if (item.href === "/") return pathname === "/";
  if (pathname === item.href || pathname.startsWith(`${item.href}/`)) return true;
  return item.activePrefixes?.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)) ?? false;
}

function NavGlyph({ name }: { name: NavIconName }) {
  if (name === "home") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4.5 10.7 12 4l7.5 6.7v8.1a1.7 1.7 0 0 1-1.7 1.7h-3.2v-5.6H9.4v5.6H6.2a1.7 1.7 0 0 1-1.7-1.7v-8.1Z" />
      </svg>
    );
  }

  if (name === "scan") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6.3 3.7h4.2v1.9H6.3v4.2H4.4V5.6c0-1.05.85-1.9 1.9-1.9Zm7.2 0h4.2c1.05 0 1.9.85 1.9 1.9v4.2h-1.9V5.6h-4.2V3.7ZM4.4 14.2h1.9v4.2h4.2v1.9H6.3a1.9 1.9 0 0 1-1.9-1.9v-4.2Zm13.3 0h1.9v4.2a1.9 1.9 0 0 1-1.9 1.9h-4.2v-1.9h4.2v-4.2ZM8 11.05h8v1.9H8v-1.9Z" />
      </svg>
    );
  }

  if (name === "price") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5.2 5.8c0-1.05.85-1.9 1.9-1.9h6.8c.5 0 .99.2 1.34.56l3.3 3.3c.36.35.56.84.56 1.34v7.8a1.9 1.9 0 0 1-1.9 1.9H7.1a1.9 1.9 0 0 1-1.9-1.9V5.8Zm8.1.1v3.3h3.3L13.3 5.9Zm-4.1 7.2h5.6v-1.7H9.2v1.7Zm0 3.1h4.1v-1.7H9.2v1.7Z" />
      </svg>
    );
  }

  const iconPaths: Record<Exclude<NavIconName, "home" | "scan" | "price">, string> = {
    more: "M5 7.5h14v2H5v-2Zm0 4h14v2H5v-2Zm0 4h14v2H5v-2Z",
    result: "M4.8 5.4c0-1 .8-1.8 1.8-1.8h10.8c1 0 1.8.8 1.8 1.8v13.2c0 1-.8 1.8-1.8 1.8H6.6c-1 0-1.8-.8-1.8-1.8V5.4Zm3.1 3.1h8.2V6.8H7.9v1.7Zm0 4.1h8.2v-1.7H7.9v1.7Zm0 4.1h5.8V15H7.9v1.7Z",
    report: "M6 3.8h8.4L19 8.4v11.8H6V3.8Zm7.6 1.8v3.6h3.6l-3.6-3.6ZM8.4 12h7.2v-1.6H8.4V12Zm0 3.3h7.2v-1.6H8.4v1.6Zm0 3.1h4.9v-1.6H8.4v1.6Z",
    docs: "M5.6 4.2h8.2l4.6 4.6v11H5.6V4.2Zm7.4 1.9v3.6h3.6L13 6.1ZM8 12.6h8v-1.5H8v1.5Zm0 3.1h8v-1.5H8v1.5Zm0 3h5.5v-1.5H8v1.5Z",
    dashboard: "M4.2 5.2h6.9v6.9H4.2V5.2Zm8.7 0h6.9v4.4h-6.9V5.2Zm0 6.2h6.9v7.4h-6.9v-7.4Zm-8.7 2.5h6.9v4.9H4.2v-4.9Z",
    saved: "M6 4h12v16l-6-3.1L6 20V4Zm2 2.1v10.5l4-2.1 4 2.1V6.1H8Z",
    risk: "M12 3.5 20.5 7v5.2c0 4.4-3.1 7.5-8.5 8.8-5.4-1.3-8.5-4.4-8.5-8.8V7L12 3.5Zm0 2.2L5.5 8.3v3.9c0 3.3 2.2 5.6 6.5 6.7 4.3-1.1 6.5-3.4 6.5-6.7V8.3L12 5.7Zm-.9 3.1h1.8v4.8h-1.8V8.8Zm0 6.4h1.8V17h-1.8v-1.8Z",
    status: "M12 4.2a7.8 7.8 0 1 1 0 15.6 7.8 7.8 0 0 1 0-15.6Zm3.9 5.1-1.2-1.2-3.8 3.8-1.6-1.6-1.2 1.2 2.8 2.8 5-5Z",
    advanced: "M12 3.6 14.2 8l4.8.7-3.5 3.4.8 4.8L12 14.6l-4.3 2.3.8-4.8L5 8.7l4.8-.7L12 3.6Z",
    payment: "M4.4 6.2c0-1 .8-1.8 1.8-1.8h11.6c1 0 1.8.8 1.8 1.8v11.6c0 1-.8 1.8-1.8 1.8H6.2c-1 0-1.8-.8-1.8-1.8V6.2Zm1.9 2v1.7h11.4V8.2H6.3Zm0 4.4v5.1h11.4v-5.1H6.3Zm1.5 2h4.9v1.4H7.8v-1.4Z",
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={iconPaths[name]} />
    </svg>
  );
}

function StatusTag({ status }: { status?: MoreItem["status"] }) {
  if (!status) return null;
  const label = status === "core" ? "Core" : status === "beta" ? "Beta" : "Setup";
  return <span className={`more-status-tag more-status-${status}`}>{label}</span>;
}

function NavLink({ item, onClick }: { item: NavItem; onClick?: () => void }) {
  const pathname = usePathname();
  return (
    <Link href={item.href} onClick={onClick} className={`nav-link nav-link-icon ${isActive(pathname, item) ? "nav-link-active" : ""}`}>
      <NavGlyph name={item.icon} />
      <span>{item.label}</span>
    </Link>
  );
}

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const isMoreActive = moreLinks.some((item) => isActive(pathname, item));

  return (
    <header className="site-header advanced-nav-header">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="brand-home-link group"
          aria-label="Open Web3Guard AI home"
          onClick={() => setOpen(false)}
        >
          <KavachWingNavLogo showText />
          <span className="brand-hover-tooltip">Web3Guard AI by RAADHANEX</span>
        </Link>

        <nav className="hidden min-w-0 flex-1 items-center justify-center gap-2 lg:flex" aria-label="Main navigation">
          {primaryLinks.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
          <details className="clean-more-menu relative">
            <summary className={`nav-link nav-link-icon cursor-pointer list-none ${isMoreActive ? "nav-link-active" : ""}`}>
              <NavGlyph name="more" />
              <span>More</span>
            </summary>
            <div className="more-menu-panel more-menu-panel-rich absolute right-0 top-12 z-50 w-[min(680px,calc(100vw-2rem))] rounded-3xl border border-white/[0.08] bg-[#050a14]/95 p-3 shadow-[0_24px_80px_rgba(0,0,0,.55)] backdrop-blur-xl">
              <div className="more-menu-head">
                <span>More tools</span>
                <p>Output, docs, saved work, and advanced setup in one clean place.</p>
              </div>
              <div className="more-menu-rich-grid">
                {moreGroups.map((group) => (
                  <section key={group.title} className="more-menu-group" aria-label={group.title}>
                    <div className="more-menu-group-head">
                      <strong>{group.title}</strong>
                      <small>{group.helper}</small>
                    </div>
                    {group.items.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className="more-menu-card"
                      >
                        <span className="more-menu-icon"><NavGlyph name={item.icon} /></span>
                        <span className="more-menu-copy">
                          <span className="more-menu-title-row">
                            <b>{item.label}</b>
                            <StatusTag status={item.status} />
                          </span>
                          <small>{item.description}</small>
                        </span>
                      </Link>
                    ))}
                  </section>
                ))}
              </div>
            </div>
          </details>
        </nav>

        <div className="hidden shrink-0 items-center gap-2 sm:flex">
          <AuthSessionButton />
        </div>

        <button
          type="button"
          aria-label="Open navigation menu"
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
          className="grid h-10 w-10 place-items-center rounded-[10px] border border-white/[0.08] bg-white/[0.04] text-white lg:hidden"
        >
          <span className="relative h-4 w-5">
            <span className={`absolute left-0 top-0 h-0.5 w-5 rounded-full bg-current transition ${open ? "translate-y-[7px] rotate-45" : ""}`} />
            <span className={`absolute left-0 top-[7px] h-0.5 w-5 rounded-full bg-current transition ${open ? "opacity-0" : ""}`} />
            <span className={`absolute left-0 top-[14px] h-0.5 w-5 rounded-full bg-current transition ${open ? "-translate-y-[7px] -rotate-45" : ""}`} />
          </span>
        </button>
      </div>

      {open ? (
        <div className="mobile-panel lg:hidden">
          <div className="mx-auto max-w-7xl px-4 pt-4 sm:px-6">
            <div className="mb-3 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
              Home shows the product overview. Scan starts the readiness flow. More keeps results, report, docs, and advanced setup easy to understand.
            </div>
            <div className="mb-3 flex justify-end">
              <AuthSessionButton />
            </div>
          </div>
          <nav className="mx-auto grid max-w-7xl gap-2 px-4 pb-4 sm:grid-cols-2 sm:px-6" aria-label="Mobile navigation">
            {primaryLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`rounded-xl border px-4 py-3 text-sm font-bold transition ${
                  isActive(pathname, item)
                    ? "border-cyan/30 bg-cyan/10 text-cyan"
                    : "border-white/[0.07] bg-white/[0.03] text-slate-300 hover:border-cyan/25 hover:text-white"
                }`}
              >
                <span className="mb-1 inline-flex h-5 w-5 text-cyan"><NavGlyph name={item.icon} /></span>
                <span className="block">{item.label}</span>
              </Link>
            ))}
            {moreGroups.map((group) => (
              <section key={group.title} className="mobile-more-group sm:col-span-2">
                <strong>{group.title}</strong>
                <div className="mt-2 grid gap-2 sm:grid-cols-3">
                  {group.items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(false)}
                      className={`mobile-more-card ${isActive(pathname, item) ? "mobile-more-card-active" : ""}`}
                    >
                      <span><NavGlyph name={item.icon} /></span>
                      <b>{item.label}</b>
                      <small>{item.description}</small>
                    </Link>
                  ))}
                </div>
              </section>
            ))}
            <Link href="/scanner/unified-url" onClick={() => setOpen(false)} className="btn-primary mt-2 sm:col-span-2">
              Start readiness scan →
            </Link>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
