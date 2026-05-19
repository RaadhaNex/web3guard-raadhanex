import { RouteLoadingShell } from "@/components/ui/RouteLoadingShell";

export default function WorkerExecutionLoading() {
  return <RouteLoadingShell title="Loading worker execution board" cards={6} />;
}
