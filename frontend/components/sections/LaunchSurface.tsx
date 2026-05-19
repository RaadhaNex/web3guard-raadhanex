import Link from "next/link";

const surfaces = [
  ["📄", "Smart Contract", "Solidity rule checks, centralization hints, and fix direction.", "/scanner/contract"],
  ["🌐", "Website Surface", "HTTPS, headers, security.txt, robots, sitemap, and trust signals.", "/scanner/website"],
  ["⚡", "dApp Frontend", "Wallet prompts, public config, chain mismatch, and transaction clarity.", "/scanner/dapp"],
  ["🔌", "API Backend", "CORS, auth, docs exposure, webhooks, rate limits, and BOLA/IDOR review.", "/scanner/api"],
  ["👛", "Wallet UX", "Approval, Permit2, spender visibility, blind signing, and chain safety.", "/scanner/wallet"],
  ["🔐", "Founder/Admin OpSec", "Multisig, timelock, signer policy, MFA, treasury, and incident response.", "/scanner/admin-opsec"],
  ["🐙", "GitHub Repo", "Public repo hygiene, Solidity discovery, package metadata, and secret hints.", "/scanner/github"],
  ["🔬", "Static Tools", "Slither/Aderyn/Mythril status stays real: installed output or clear not assessed.", "/scanner/static-analysis"],
  ["📋", "Launch Evidence", "Pre-audit pack, bug bounty readiness, deployment checklist, and disclosures.", "/launch-readiness"],
];

export function LaunchSurface() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto mb-10 max-w-3xl text-center">
        <p className="section-label justify-center">Full launch surface</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Web3 launch risk goes beyond smart contracts.</h2>
        <p className="mt-4 text-sm leading-7 text-slate-400">
          Web3Guard maps the public launch surface founders usually miss: contracts, website trust, wallet UX, admin keys, GitHub hygiene, and external-tool readiness.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {surfaces.map(([icon, title, description, href]) => (
          <Link
            key={title}
            href={href}
            className="group flex gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 transition hover:-translate-y-0.5 hover:border-cyan/30 hover:bg-cyan/[0.035] hover:shadow-[0_18px_60px_rgba(6,182,212,.09)]"
          >
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[12px] border border-cyan/20 bg-cyan/[0.07] text-xl shadow-[inset_0_1px_0_rgba(255,255,255,.05)]">
              {icon}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-black text-white">{title}</span>
              <span className="mt-1 block text-xs leading-5 text-slate-400">{description}</span>
            </span>
            <span className="mt-1 text-slate-600 transition group-hover:translate-x-0.5 group-hover:text-cyan">→</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
