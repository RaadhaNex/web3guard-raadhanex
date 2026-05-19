import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Loading launch validation sprint"
      title="Preparing launch compression checks"
      description="Loading Slither readiness, Razorpay readiness, and dependency intelligence controls."
    />
  );
}
