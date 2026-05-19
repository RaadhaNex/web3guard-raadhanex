import Link from "next/link";
import { TrustCard, TrustHero } from "@/components/ui/TrustPage";

const samples = [
  {
    title: "Token launch pre-audit readiness",
    scores: ["Website Surface: 82", "Contract Rule: Not Assessed", "Launch Evidence: 43", "Overall Confidence: Partial"],
    notes: ["Website headers and policy pages were assessed.", "Contract source was not provided, so no contract score was invented.", "Admin OpSec and wallet flow evidence are required before launch claims."],
  },
  {
    title: "dApp frontend + GitHub readiness",
    scores: ["Website Surface: 76", "Contract Rule: 68", "Launch Evidence: 71", "Overall Confidence: Evidence Needed"],
    notes: ["Public repo scanned read-only.", "Solidity rule engine found medium/high fix areas.", "External Slither/Aderyn/Mythril status remained Tool Not Installed."],
  },
  {
    title: "Founder/admin OpSec snapshot",
    scores: ["Website Surface: Not Assessed", "Contract Rule: Not Assessed", "Launch Evidence: 58", "Overall Confidence: Manual Review Needed"],
    notes: ["Multisig/timelock evidence was missing.", "MFA and incident response checklist generated.", "No wallet signing or private-key collection was performed."],
  },
];

export default function SampleReportsPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Sample reports" title="Report examples with realistic evidence language." text="Samples show structure and safe wording. They are not real customer audits and do not claim certification or 100% security." />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-3">
          {samples.map((sample) => (
            <TrustCard key={sample.title} title={sample.title} tone="yellow">
              <div className="flex flex-wrap gap-2">
                {sample.scores.map((score) => <span key={score} className="rounded-full border border-white/10 bg-black/30 px-3 py-1 text-xs font-black text-slate-100">{score}</span>)}
              </div>
              <ul className="mt-5 space-y-2">
                {sample.notes.map((note) => <li key={note}>• {note}</li>)}
              </ul>
            </TrustCard>
          ))}
        </div>
        <div className="mt-10 flex flex-wrap gap-3"><Link href="/scanner/unified-url" className="btn-primary">Generate real report</Link><Link href="/methodology" className="btn-secondary">Read methodology</Link></div>
      </div>
    </main>
  );
}
