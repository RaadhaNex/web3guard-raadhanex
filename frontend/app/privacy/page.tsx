export default function PrivacyPage() {
  const points = [
    "MVP stores leads, contact details, package selection, payment reference, and admin notes in local JSONL files.",
    "Do not paste secrets, private keys, seed phrases, or production credentials into scanner inputs.",
    "AI is optional and backend-only. Frontend must never store AI API keys.",
    "Default safe setting should avoid sending full source code to third-party AI providers unless explicitly enabled later.",
    "Production upgrade should use encrypted database storage, access controls, audit logs, retention limits, export, and deletion workflow.",
  ];
  return (
    <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Privacy</p>
      <h1 className="mt-3 text-4xl font-black sm:text-5xl">Privacy and data handling policy.</h1>
      <p className="mt-4 text-slate-400">This MVP is designed for local testing and early paid-review leads. Production should harden storage, auth, encryption, and retention before public scale.</p>
      <div className="card mt-10 p-6"><ul className="space-y-4 text-sm leading-6 text-slate-300">{points.map((x) => <li key={x}>• {x}</li>)}</ul></div>
    </div>
  );
}
