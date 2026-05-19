import { DashboardWorkflowClient } from "@/components/dashboard/DashboardWorkflowClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function DashboardWorkflowPage() {
  return <DashboardWorkflowClient />;
}
