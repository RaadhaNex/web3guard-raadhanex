import { BlockedClaimsBox, TrustCard, TrustHero, TrustList } from "@/components/ui/TrustPage";

const responsibleUse = [
  "Only scan assets you own or are authorized to review.",
  "Use passive URL checks and read-only repository/address lookups for public beta workflows.",
  "Do not paste private keys, seed phrases, mnemonics, production credentials, or sensitive customer data.",
  "Do not use scanner output to harass, exploit, or publicly accuse third-party projects.",
  "Report suspected platform security issues through the project contact/security.txt path once configured.",
];

const platformControls = [
  "Supabase Auth and protected dashboard flow stay preserved from the current codebase.",
  "FastAPI docs are disabled in production/staging by backend configuration.",
  "Security headers middleware remains backend-side; frontend CSP/domain hardening should be verified after custom domain setup.",
  "Report exports carry disclaimers and blocked wording rules.",
  "External providers are marked Needs API Key / Provider Not Configured when missing.",
];

export default function SecurityPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Security" title="Responsible-use and platform security stance." text="Public beta is designed for defensive pre-launch readiness. It avoids wallet signing, private-key collection, exploit automation, and fake provider output." />
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-12 sm:px-6 lg:grid-cols-2 lg:px-8">
        <TrustCard title="Responsible use" tone="green"><TrustList items={responsibleUse} /></TrustCard>
        <TrustCard title="Current platform controls"><TrustList items={platformControls} /></TrustCard>
        <TrustCard title="security.txt recommendation" tone="yellow"><p>Add <code>/.well-known/security.txt</code> using the free generator before public launch, then link it from this page.</p></TrustCard>
        <BlockedClaimsBox />
      </div>
    </main>
  );
}
