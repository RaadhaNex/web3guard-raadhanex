import { ProductionQaClient } from "@/components/professional-production-qa/ProductionQaClient";

export const metadata = {
  title: "Production QA | Web3Guard AI",
  description: "Phase U first real production QA, launch checklist, and competitor-position dashboard.",
  robots: { index: false, follow: false },
};

export default function ProfessionalProductionQaPage() {
  return <ProductionQaClient />;
}
