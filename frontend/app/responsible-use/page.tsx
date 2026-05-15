export default function ResponsibleUsePage() {
  const allowed = [
    "Scanning your own smart contract code",
    "Running passive website checks on projects you own or are authorized to review",
    "Using checklist modules for your own dApp/API/wallet/admin setup",
    "Preparing a project before professional audit, contest, or bug bounty",
    "Requesting paid manual review with clear scope and authorization",
  ];
  const notAllowed = [
    "Scanning third-party websites without authorization",
    "Trying to bypass login, admin panels, wallets, or rate limits",
    "Using outputs to attack, exploit, extort, or harass projects",
    "Submitting stolen/private code or secrets",
    "Asking for exploit automation or destructive testing against real targets",
  ];
  return (
    <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Responsible use</p>
      <h1 className="mt-3 text-4xl font-black sm:text-5xl">Use Web3Guard AI only on authorized projects.</h1>
      <p className="mt-4 max-w-3xl text-slate-400">This platform is built for defensive launch readiness. It must not be used for unauthorized probing, exploitation, or destructive security activity.</p>
      <div className="mt-10 grid gap-5 md:grid-cols-2">
        <div className="card p-6"><h2 className="text-2xl font-black">Allowed</h2><ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">{allowed.map((x) => <li key={x}>✓ {x}</li>)}</ul></div>
        <div className="card p-6"><h2 className="text-2xl font-black">Not allowed</h2><ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">{notAllowed.map((x) => <li key={x}>✕ {x}</li>)}</ul></div>
      </div>
      <div className="mt-8 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100">Deep website/infrastructure scanning must require future ownership verification and written scope.</div>
    </div>
  );
}
