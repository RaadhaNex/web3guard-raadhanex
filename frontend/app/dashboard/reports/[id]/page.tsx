import { ReportDetailClient } from "@/components/dashboard/ReportDetailClient";

export default function ReportDetailPage({ params }: { params: { id: string } }) {
  return <ReportDetailClient reportId={params.id} />;
}
