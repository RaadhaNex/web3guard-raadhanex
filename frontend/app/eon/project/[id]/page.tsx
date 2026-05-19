import { EonClient } from "@/components/eon/EonClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function EonProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const paramsValue = await params;
  return <EonClient projectId={paramsValue.id} />;
}
