import { BlockedClaimsBox, TrustCard, TrustHero, TrustList } from "@/components/ui/TrustPage";

const notDone = [
  "No certified audit or full manual audit claim is produced by automated scans.",
  "No exploit automation, brute force, destructive testing, wallet signing, or mainnet transaction execution is performed.",
  "No private key, seed phrase, mnemonic, or wallet-signing collection is allowed.",
  "AI provider is OFF unless configured with real backend env and clear data-sharing policy.",
  "Slither, Aderyn, Mythril, Manticore, Echidna, and Semgrep only run if real tools/workers are installed and enabled.",
  "Payment/Razorpay/UPI activation is deferred to the final payment phase.",
];

const needsEvidence = [
  "Website scan: public URL, headers, HTML hints, policy pages, and passive checks only.",
  "Contract score: pasted Solidity or verified explorer source. Otherwise contract stays Not Assessed.",
  "Wallet flow: UX/source/checklist evidence. URL-only scans cannot prove wallet safety.",
  "Admin OpSec: multisig, timelock, owner roles, MFA, key policy, and incident process evidence.",
  "GitHub: public repo URL or configured authorized access. No private repo guessing.",
];

export default function LimitationsPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Limitations" title="Honest scanner boundaries for public beta." text="Web3Guard AI is useful for pre-audit cleanup and launch readiness, but it must not pretend missing evidence, disabled providers, or automated checks are a complete audit." />
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-12 sm:px-6 lg:grid-cols-2 lg:px-8">
        <TrustCard title="What this beta does not do" tone="yellow"><TrustList items={notDone} /></TrustCard>
        <TrustCard title="Evidence needed for deeper results"><TrustList items={needsEvidence} /></TrustCard>
        <TrustCard title="How Not Assessed works" tone="green">
          <p>Any module without real input remains <strong>Not Assessed</strong>. Reports may show an available partial score for assessed modules, but that is not a full audit score and not a guarantee of launch safety.</p>
        </TrustCard>
        <BlockedClaimsBox />
      </div>
    </main>
  );
}
