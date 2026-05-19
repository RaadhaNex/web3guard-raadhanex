import { EonClient } from "@/components/eon/EonClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function EonPage() {
  return <EonClient />;
}
