import { PublicTrustProjectClient } from "@/components/trust/PublicTrustClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function TrustProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const paramsValue = await params;
  return <PublicTrustProjectClient projectId={paramsValue.id} />;
}
