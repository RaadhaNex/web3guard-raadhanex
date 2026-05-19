import { TrustReadinessClient } from "@/components/trust-readiness/TrustReadinessClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function TrustReadinessPage() {
  return <TrustReadinessClient />;
}
