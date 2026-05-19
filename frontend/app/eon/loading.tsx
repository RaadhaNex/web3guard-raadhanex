import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function Loading() {
  return (
    <RouteLoadingShell
      label="EON route loading"
      title="Loading EON risk graph"
      description="Preparing launch blockers, evidence ledger, and next-best-action panels."
    />
  );
}
