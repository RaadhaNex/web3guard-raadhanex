import { CommunityReviewClient } from "@/components/community-review/CommunityReviewClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function CommunityReviewAdminPage() {
  return <CommunityReviewClient adminMode />;
}
