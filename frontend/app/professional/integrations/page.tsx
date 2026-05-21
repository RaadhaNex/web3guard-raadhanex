import { ProfessionalOpsConsoleClient } from "@/components/professional-ops/ProfessionalOpsConsoleClient";

export const metadata = {
  title: "Professional Integrations | Web3Guard AI",
  description: "Phase O/P GitHub and on-chain provider webhook setup console for real monitoring evidence.",
};

export default function ProfessionalIntegrationsPage() {
  return <ProfessionalOpsConsoleClient mode="integrations" />;
}
