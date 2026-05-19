import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="Copilot route loading"
      title="Loading security copilot"
      description="Preparing safe guidance, local checklist fallback, and report wording helpers."
    />
  );
}
