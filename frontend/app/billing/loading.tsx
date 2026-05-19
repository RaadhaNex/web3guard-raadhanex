import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Billing route loading"
      title="Loading billing workspace"
      description="Preparing Razorpay/UPI verified billing status without changing payment data."
    />
  );
}
