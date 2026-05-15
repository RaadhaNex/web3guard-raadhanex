import { WorkspaceDetailClient } from "@/components/workspace/WorkspaceDetailClient";

export default async function WorkspaceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const paramsValue = await params;

  return <WorkspaceDetailClient organizationId={paramsValue.id} />;
}
