import { DashboardWorkflowClient } from "@/components/dashboard/DashboardWorkflowClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type Props = {
  params: Promise<{ id: string }>;
};

export default async function ProjectWorkflowPage({ params }: Props) {
  const { id } = await params;
  return <DashboardWorkflowClient projectId={id} />;
}
