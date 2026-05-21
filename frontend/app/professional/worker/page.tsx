import { ProfessionalOpsConsoleClient } from "@/components/professional-ops/ProfessionalOpsConsoleClient";

export const metadata = {
  title: "Formal/Fuzz Worker | Web3Guard AI",
  description: "Phase Q safe isolated Foundry/Echidna worker runner console. Disabled by default until explicitly configured.",
};

export default function ProfessionalWorkerPage() {
  return <ProfessionalOpsConsoleClient mode="worker" />;
}
