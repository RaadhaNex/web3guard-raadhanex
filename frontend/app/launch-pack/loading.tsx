import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function LaunchPackLoading() {
  return (
    <RouteLoadingShell
      label="Loading MVP launch pack"
      title="Preparing launch checklist, outreach kit, and first-user tracker."
      description="This route keeps the final launch sprint lightweight while API data loads."
    />
  );
}
