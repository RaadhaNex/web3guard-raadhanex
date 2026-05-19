import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function PaymentValidationLoading() {
  return <RouteLoadingShell title="Loading payment validation" description="Checking Razorpay, UPI, access gates, and first paid flow..." />;
}
