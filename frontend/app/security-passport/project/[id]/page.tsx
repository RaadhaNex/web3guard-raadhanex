import { SecurityPassportClient } from "@/components/security-passport/SecurityPassportClient";

type SecurityPassportProjectPageProps = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ user_id?: string | string[] }>;
};

export default async function SecurityPassportProjectPage({
  params,
  searchParams,
}: SecurityPassportProjectPageProps) {
  const { id } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const rawUserId = resolvedSearchParams.user_id;
  const initialUserId = Array.isArray(rawUserId) ? rawUserId[0] || "" : rawUserId || "";

  return <SecurityPassportClient mode="project" projectId={id} initialUserId={initialUserId} />;
}
