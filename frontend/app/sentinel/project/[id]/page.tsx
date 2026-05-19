import { SentinelClient } from "@/components/sentinel/SentinelClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function SentinelProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SentinelClient mode="project" projectId={id} />;
}
