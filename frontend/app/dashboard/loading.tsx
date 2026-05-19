import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Dashboard route loading"
      title="Loading dashboard"
      description="Preparing projects, scans, reports, and workspace navigation."
    />
  );
}
