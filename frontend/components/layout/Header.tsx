"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthSessionButton } from "@/components/auth/AuthSessionButton";
import KavachWingNavLogo from "@/components/brand/KavachWingNavLogo";

type NavIconName = "home" | "scan" | "price" | "more";

type NavItem = {
  href: string;
  label: string;
  icon: NavIconName;
  activePrefixes?: string[];
};

const primaryLinks: NavItem[] = [
  { href: "/", label: "Home", icon: "home" },
  { href: "/scanner/unified-url", label: "Scan", icon: "scan", activePrefixes: ["/scanner"] },
  { href: "/pricing", label: "Price", icon: "price" },
];

const secondaryLinks = [
  { href: "/results", label: "Results" },
  { href: "/report", label: "Report" },
  { href: "/docs", label: "Docs" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/scans", label: "Saved scans" },
  { href: "/risk-intelligence", label: "Risk intelligence" },
  { href: "/payment-validation", label: "Payment validation" },
  { href: "/feature-status", label: "Feature status" },
  { href: "/advanced", label: "Advanced tools" },
] as const;

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

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 7.5h14v2H5v-2Zm0 4h14v2H5v-2Zm0 4h14v2H5v-2Z" />
    </svg>
  );
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
  const isMoreActive = secondaryLinks.some((item) => isActive(pathname, item));

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
            <div className="more-menu-panel absolute right-0 top-12 z-50 w-72 rounded-2xl border border-white/[0.08] bg-[#050a14]/95 p-2 shadow-[0_24px_80px_rgba(0,0,0,.55)] backdrop-blur-xl">
              {secondaryLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="block rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-300 transition hover:bg-white/[0.05] hover:text-white"
                >
                  {item.label}
                </Link>
              ))}
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
              Home shows the Web3Guard overview. Scan starts the readiness flow. Results, reports, docs, and advanced tools stay under More.
            </div>
            <div className="mb-3 flex justify-end">
              <AuthSessionButton />
            </div>
          </div>
          <nav className="mx-auto grid max-w-7xl gap-2 px-4 pb-4 sm:grid-cols-2 sm:px-6" aria-label="Mobile navigation">
            {[...primaryLinks, ...secondaryLinks].map((item) => (
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
                {item.label}
              </Link>
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
