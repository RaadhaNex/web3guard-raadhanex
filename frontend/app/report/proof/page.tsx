import { PublicProofReportsClient } from "@/components/public-proof/PublicProofReportsClient";

export const metadata = {
  title: "Public Proof Reports | Web3Guard AI",
  description: "Draft, approve, publish, verify, and revoke evidence-first pre-audit proof packets without certified-audit claims.",
};

export default function PublicProofReportsPage() {
  return <PublicProofReportsClient />;
}
