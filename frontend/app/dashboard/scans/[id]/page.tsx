import { ScanDetailClient } from "@/components/dashboard/ScanDetailClient";

export default function ScanDetailPage({ params }: { params: { id: string } }) {
  return <ScanDetailClient scanId={params.id} />;
}
