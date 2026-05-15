import { ReportDetailClient } from "@/components/dashboard/ReportDetailClient";

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const paramsValue = await params;

  return <ReportDetailClient reportId={paramsValue.id} />;
}