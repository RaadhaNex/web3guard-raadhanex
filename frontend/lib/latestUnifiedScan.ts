import type { UnifiedUrlScanResponse } from "@/lib/types";

export const LATEST_UNIFIED_SCAN_KEY = "web3guard.latestUnifiedScan.v1";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function looksLikeLatestUnifiedScan(value: unknown): value is UnifiedUrlScanResponse {
  if (!isRecord(value)) return false;
  return (
    typeof value.report_id === "string" &&
    typeof value.website_url === "string" &&
    Array.isArray(value.module_cards) &&
    isRecord(value.combined_report)
  );
}

export function saveLatestUnifiedScan(result: UnifiedUrlScanResponse) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LATEST_UNIFIED_SCAN_KEY, JSON.stringify(result));
  } catch {
    // Local storage can be blocked by the browser. Scanner result still remains visible in memory.
  }
}

export function loadLatestUnifiedScan(): UnifiedUrlScanResponse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(LATEST_UNIFIED_SCAN_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return looksLikeLatestUnifiedScan(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function clearLatestUnifiedScan() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(LATEST_UNIFIED_SCAN_KEY);
  } catch {
    // Ignore browser storage errors.
  }
}
