import { BlockedClaimsBox, TrustCard, TrustHero, TrustList } from "@/components/ui/TrustPage";

const terms = [
  "Web3Guard AI provides preliminary security readiness guidance only.",
  "Automated scanner output is not a certified audit, penetration test, legal opinion, financial advice, or guarantee of security.",
  "Users must confirm they own or are authorized to review submitted URLs, repositories, contracts, and code.",
  "No wallet signing, private-key collection, seed phrase collection, or exploit automation is part of the service.",
  "Paid plans remain request-only until the final payment phase verifies real UPI/Razorpay order, checkout, webhook, and audit logs.",
  "RAADHANEX may reject unsafe, unauthorized, illegal, or out-of-scope requests.",
];

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Terms" title="Public beta terms summary." text="These terms keep the beta honest while legal-reviewed production terms are prepared." />
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-12 sm:px-6 lg:grid-cols-2 lg:px-8">
        <TrustCard title="Use rules" tone="green"><TrustList items={terms} /></TrustCard>
        <BlockedClaimsBox />
      </div>
    </main>
  );
}
