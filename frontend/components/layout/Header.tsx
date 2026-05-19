"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthSessionButton } from "@/components/auth/AuthSessionButton";
import KavachWingNavLogo from "@/components/brand/KavachWingNavLogo";

type NavItem = {
  href: string;
  label: string;
  activePrefixes?: string[];
};

const primaryLinks: NavItem[] = [
  { href: "/", label: "Home" },
  { href: "/scanner/unified-url", label: "Scan", activePrefixes: ["/scanner"] },
  { href: "/pricing", label: "Price" },
];

const secondaryLinks: NavItem[] = [
  { href: "/results", label: "Results" },
  { href: "/report", label: "Report" },
  { href: "/docs", label: "Docs" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/scans", label: "Saved scans" },
  { href: "/launch-pack", label: "First 10 users" },
  { href: "/risk-intelligence", label: "Risk intelligence" },
  { href: "/payment-validation", label: "Payment validation" },
  { href: "/feature-status", label: "Feature status" },
  { href: "/advanced", label: "Advanced tools" },
  { href: "/settings/language", label: "Settings" },
];

function isActive(pathname: string, item: NavItem) {
  if (item.href === "/") return pathname === "/";
  if (pathname === item.href || pathname.startsWith(`${item.href}/`)) return true;
  return item.activePrefixes?.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)) ?? false;
}

function NavLink({ item, onClick }: { item: NavItem; onClick?: () => void }) {
  const pathname = usePathname();
  return (
    <Link href={item.href} onClick={onClick} className={`nav-link ${isActive(pathname, item) ? "nav-link-active" : ""}`}>
      {item.label}
    </Link>
  );
}

function SettingsIcon() {
  return (
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 15.4a3.4 3.4 0 1 0 0-6.8 3.4 3.4 0 0 0 0 6.8Z"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M19.4 13.5c.08-.48.1-.99.1-1.5s-.02-1.02-.1-1.5l2.03-1.56-1.92-3.32-2.4.97a7.65 7.65 0 0 0-2.6-1.5L14.16 2h-3.84l-.35 3.09a7.65 7.65 0 0 0-2.6 1.5l-2.4-.97-1.92 3.32L5.08 10.5c-.08.48-.1.99-.1 1.5s.02 1.02.1 1.5l-2.03 1.56 1.92 3.32 2.4-.97a7.65 7.65 0 0 0 2.6 1.5l.35 3.09h3.84l.35-3.09a7.65 7.65 0 0 0 2.6-1.5l2.4.97 1.92-3.32-2.03-1.56Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const isMoreActive = secondaryLinks.some((item) => isActive(pathname, item));
  const settingsItem: NavItem = { href: "/settings/language", label: "Settings" };

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

        <nav className="hidden min-w-0 flex-1 items-center justify-center gap-1 lg:flex" aria-label="Main navigation">
          {primaryLinks.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
          <details className="clean-more-menu relative">
            <summary className={`nav-link cursor-pointer list-none ${isMoreActive ? "nav-link-active" : ""}`}>
              More
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
          <Link
            href="/settings/language"
            className={`settings-orb ${isActive(pathname, settingsItem) ? "settings-orb-active" : ""}`}
            aria-label="Open settings"
            title="Settings"
          >
            <SettingsIcon />
          </Link>
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
              Home explains Web3Guard. Scan starts the core readiness flow. Results, reports, docs, and advanced tools stay under More.
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
