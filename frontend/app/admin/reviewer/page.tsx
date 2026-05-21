import { ProfessionalOpsConsoleClient } from "@/components/professional-ops/ProfessionalOpsConsoleClient";

export const metadata = {
  title: "Reviewer Onboarding | Web3Guard AI Admin",
  description: "Phase R reviewer and auditor onboarding gates for human-reviewed pre-audit workflows.",
  robots: { index: false, follow: false },
};

export default function AdminReviewersPage() {
  return <ProfessionalOpsConsoleClient mode="reviewers" />;
}
