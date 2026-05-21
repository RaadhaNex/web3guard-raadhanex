import { ProfessionalOpsConsoleClient } from "@/components/professional-ops/ProfessionalOpsConsoleClient";

export const metadata = {
  title: "Client Report Delivery | Web3Guard AI",
  description: "Phase S client-facing professional delivery packets with integrity hash and safe pre-audit wording.",
};

export default function ReportDeliveryPage() {
  return <ProfessionalOpsConsoleClient mode="delivery" />;
}
