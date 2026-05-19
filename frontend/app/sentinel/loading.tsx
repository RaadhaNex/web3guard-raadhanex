import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Sentinel route loading"
      title="Loading Sentinel monitoring"
      description="Preparing monitoring and vulnerability intelligence panels without fake live results."
    />
  );
}
