import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Passport route loading"
      title="Loading security passport"
      description="Preparing trust snapshots, evidence summary, and real external links only."
    />
  );
}
