import { CommunityReviewClient } from "@/components/community-review/CommunityReviewClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function CommunityReviewProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CommunityReviewClient defaultProjectId={id} />;
}
