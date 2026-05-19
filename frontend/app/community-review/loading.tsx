import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Community route loading"
      title="Loading community review layer"
      description="Preparing review requests, triage queues, and safe feedback workflow."
    />
  );
}
