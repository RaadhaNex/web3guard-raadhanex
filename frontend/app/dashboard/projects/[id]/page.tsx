import { ProjectDetailClient } from "@/components/dashboard/ProjectDetailClient";

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const paramsValue = await params;

  return <ProjectDetailClient projectId={paramsValue.id} />;
}