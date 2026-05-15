import { ScanDetailClient } from "@/components/dashboard/ScanDetailClient";

export default async function ScanDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const paramsValue = await params;

  return <ScanDetailClient scanId={paramsValue.id} />;
}