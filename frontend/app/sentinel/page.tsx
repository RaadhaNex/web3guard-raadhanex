import { SentinelClient } from "@/components/sentinel/SentinelClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function SentinelPage() {
  return <SentinelClient mode="overview" />;
}
