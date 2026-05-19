import { TrustCard, TrustHero } from "@/components/ui/TrustPage";

const changes = [
  ["Public beta readiness patch", "Added trust pages, evidence-first report split, free founder tools, integration readiness status, and premium black/charcoal UI system."],
  ["Report realism", "Reports split Website Surface Score, Contract Rule Score, Launch Evidence Score, and Overall Launch Confidence without calling it a full audit score."],
  ["Direct exports", "Scanner result exports remain PDF, HTML, Markdown, and JSON. Missing modules stay Not Assessed in exports."],
  ["Payment verification final", "Razorpay/UPI billing now uses backend-created orders, signature/webhook verification, audit logs, and manual UPI fallback. Paid access still never unlocks from frontend-only state."],
  ["External tools", "Slither/Aderyn/Mythril and AI provider remain honest status-only unless real tools/API keys are configured."],
];

export default function ChangelogPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Changelog" title="Public beta changes without fake launch claims." text="This page tracks product readiness changes in plain language so users can see what is live, deferred, or evidence-dependent." />
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="space-y-4">
          {changes.map(([title, text]) => (
            <TrustCard key={title} title={title}><p>{text}</p></TrustCard>
          ))}
        </div>
      </div>
    </main>
  );
}
