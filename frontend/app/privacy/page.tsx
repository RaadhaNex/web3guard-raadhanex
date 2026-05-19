import { TrustCard, TrustHero, TrustList } from "@/components/ui/TrustPage";

const policy = [
  "Do not paste private keys, seed phrases, mnemonics, production credentials, or sensitive customer data into scanner inputs.",
  "Scanner inputs may be sent to the FastAPI backend for analysis and optional dashboard history when the user is logged in.",
  "Supabase Auth/database storage depends on deployed environment configuration; local JSONL fallback may exist in development.",
  "AI provider is OFF by default. Frontend must never store provider API keys.",
  "External provider data is fetched only when the matching backend provider is configured; missing providers produce honest status messages.",
  "Before public scale, define retention limits, deletion workflow, admin access review, and audit logging policy.",
];

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Privacy" title="Privacy rules for scanner input and beta data." text="The safest public beta posture is simple: no secrets, no private wallet material, no fake provider calls, and clear separation of local/dev storage from production Supabase storage." />
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8"><TrustCard title="Data handling baseline" tone="yellow"><TrustList items={policy} /></TrustCard></div>
    </main>
  );
}
