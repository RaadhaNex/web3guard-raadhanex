import Link from "next/link";
import { AuthSessionButton } from "@/components/auth/AuthSessionButton";
import { brand } from "@/lib/constants";

const visibleNav = [
  { href: "/scanner/unified-url", label: "URL Scan" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/report/professional", label: "Reports" },
  { href: "/pricing", label: "Pricing" },
];

const moreGroups = [
  {
    title: "Scanner modules",
    links: [
      { href: "/scanner/contract", label: "Contract" },
      { href: "/scanner/website", label: "Website" },
      { href: "/scanner/website-advanced", label: "Website Advanced" },
      { href: "/scanner/dapp", label: "dApp" },
      { href: "/scanner/api", label: "API" },
      { href: "/scanner/api-deep", label: "API Deep" },
      { href: "/scanner/wallet", label: "Wallet" },
      { href: "/scanner/admin-opsec", label: "Admin OpSec" },
    ],
  },
  {
    title: "Security engines",
    links: [
      { href: "/scanner/static-analysis", label: "Static Tools" },
      { href: "/scanner/deep-analysis", label: "Deep Analysis" },
      { href: "/scanner/address", label: "Address Scan" },
      { href: "/scanner/github", label: "GitHub Scan" },
      { href: "/scanner/permission-map", label: "Permissions" },
      { href: "/scanner/launch-transparency", label: "Launch Transparency" },
      { href: "/scanner/contract-diff", label: "Contract Diff" },
      { href: "/scanner/upgrade-safety", label: "Upgrade Safety" },
      { href: "/scanner/wallet-risk", label: "Wallet Risk" },
      { href: "/scanner/cross-chain", label: "Cross-chain" },
    ],
  },
  {
    title: "Operations",
    links: [
      { href: "/ai-fix-assistant", label: "AI Fix" },
      { href: "/monitoring", label: "Monitoring" },
      { href: "/threat-intel", label: "Threat Intel" },
      { href: "/bug-bounty", label: "Bounty" },
      { href: "/registry", label: "Registry" },
      { href: "/developer-api", label: "Developer API" },
      { href: "/cicd", label: "CI/CD" },
      { href: "/notifications", label: "Notify" },
      { href: "/compliance", label: "Compliance" },
      { href: "/security-hardening", label: "Security" },
    ],
  },
  {
    title: "Trust & resources",
    links: [
      { href: "/feature-status", label: "Feature Status" },
      { href: "/methodology", label: "Methodology" },
      { href: "/sample-reports", label: "Samples" },
      { href: "/trust", label: "Trust Policy" },
      { href: "/learning", label: "Learning" },
      { href: "/launch-pack", label: "Launch Pack" },
    ],
  },
];

const mobileQuickNav = [
  { href: "/scanner/unified-url", label: "Scan" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/pricing", label: "Pricing" },
  { href: "/report/professional", label: "Reports" },
];

function MoreMenu({ compact = false }: { compact?: boolean }) {
  return (
    <details className="nav-more group relative">
      <summary className={compact ? "nav-pill cursor-pointer list-none" : "nav-link cursor-pointer list-none"}>
        More
        <span aria-hidden="true" className="ml-1 inline-block transition group-open:rotate-180">⌄</span>
      </summary>
      <div className="nav-more-panel">
        {moreGroups.map((group) => (
          <div key={group.title} className="min-w-0">
            <p className="nav-more-title">{group.title}</p>
            <div className="mt-2 grid gap-1">
              {group.links.map((item) => (
                <Link key={item.href} href={item.href} className="nav-more-link">
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}

export function Header() {
  return (
    <header className="site-header sticky top-0 z-50 border-b backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3" aria-label="Web3Guard AI home">
          <span className="brand-mark flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-2xl border shadow-soft">
            <img src="/raadhanex-logo.svg" alt="" className="h-full w-full object-cover" />
          </span>
          <span className="hidden min-w-0 sm:block">
            <span className="brand-product block truncate text-sm font-black tracking-wide">{brand.product}</span>
            <span className="brand-company block truncate text-xs">by {brand.company}</span>
          </span>
        </Link>

        <nav className="hidden min-w-0 flex-1 items-center justify-center gap-1 text-sm lg:flex" aria-label="Main navigation">
          {visibleNav.map((item) => (
            <Link key={item.href} href={item.href} className="nav-link">
              {item.label}
            </Link>
          ))}
          <MoreMenu />
        </nav>

        <div className="hidden shrink-0 items-center gap-2 sm:flex">
          <AuthSessionButton />
        </div>
      </div>

      <nav className="scrollbar-hide flex items-center gap-2 overflow-x-auto border-t px-4 py-2 text-xs lg:hidden" aria-label="Mobile quick navigation">
        {mobileQuickNav.map((item) => (
          <Link key={item.href} href={item.href} className="nav-pill">
            {item.label}
          </Link>
        ))}
        <MoreMenu compact />
      </nav>
    </header>
  );
}
