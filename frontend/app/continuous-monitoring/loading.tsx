import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Monitoring route loading"
      title="Loading monitoring workspace"
      description="Preparing stale report checks and manual/scheduled recheck status."
    />
  );
}
