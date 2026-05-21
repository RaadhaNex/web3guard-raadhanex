import { RealSetupAssistantClient } from "@/components/professional-setup/RealSetupAssistantClient";

export const metadata = {
  title: "Real Setup Assistant | Web3Guard AI",
  description: "Phase T production readiness, env checklist, webhook setup, and safe worker gate.",
  robots: { index: false, follow: false },
};

export default function ProfessionalSetupPage() {
  return <RealSetupAssistantClient />;
}
