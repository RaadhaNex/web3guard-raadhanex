import { ProfessionalOpsConsoleClient } from "@/components/professional-ops/ProfessionalOpsConsoleClient";

export const metadata = {
  title: "Professional Monitoring | Web3Guard AI",
  description: "Phase N professional monitoring dashboard for baselines, drift events, and continuous assurance readiness.",
};

export default function ProfessionalMonitoringPage() {
  return <ProfessionalOpsConsoleClient mode="monitoring" />;
}
