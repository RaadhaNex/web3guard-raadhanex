import { WorkspaceDetailClient } from "@/components/workspace/WorkspaceDetailClient";

export default function WorkspaceDetailPage({ params }: { params: { id: string } }) {
  return <WorkspaceDetailClient organizationId={params.id} />;
}
