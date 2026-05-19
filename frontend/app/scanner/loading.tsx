import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Scanner route loading"
      title="Loading scanner workspace"
      description="Starting the passive, permission-based launch readiness console."
    />
  );
}
