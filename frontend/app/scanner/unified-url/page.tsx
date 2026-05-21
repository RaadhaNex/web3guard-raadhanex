import { UnifiedUrlScannerClient } from "@/components/scanner/UnifiedUrlScannerClient";

export const metadata = {
  title: "Start Scan | Web3Guard AI",
  description: "Submit your Web3 project URL, contract, GitHub, API, or Solidity source for launch readiness assessment. Evidence-only. Not a certified audit.",
};

export default function UnifiedUrlScannerPage() {
  return <UnifiedUrlScannerClient />;
}
