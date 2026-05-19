import { FreeToolsClient } from "@/components/tools/FreeToolsClient";
import { TrustHero } from "@/components/ui/TrustPage";

export default function FreeToolsPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Free value" title="Useful Web3 launch tools before paid phases." text="Generate founder/admin OpSec checklists, wallet UX safety notes, security.txt, robots guidance, testing templates, pre-audit packs, bug bounty readiness, and CI starter workflows without fake integrations." />
      <FreeToolsClient />
    </main>
  );
}
