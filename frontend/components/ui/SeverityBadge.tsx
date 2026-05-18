import type { Severity } from "@/lib/types";

const cls: Record<Severity, string> = {
  critical: "sev-critical",
  high:     "sev-high",
  medium:   "sev-medium",
  low:      "sev-low",
  info:     "sev-info",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={cls[severity] ?? "sev-info"}>
      {severity}
    </span>
  );
}
