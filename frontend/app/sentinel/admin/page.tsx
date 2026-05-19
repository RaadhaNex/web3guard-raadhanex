import { SentinelClient } from "@/components/sentinel/SentinelClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function SentinelAdminPage() {
  return <SentinelClient mode="admin" />;
}
