import { getCurrentUserId, getSessionToken } from "@/lib/supabase";

export async function currentDashboardUser() {
  const userId = await getCurrentUserId();
  const token = await getSessionToken();
  return { userId, headers: token ? { Authorization: `Bearer ${token}` } : undefined };
}

export function fmtDate(value?: string | null) {
  if (!value) return "No date";
  try { return new Date(value).toLocaleString(); } catch { return value; }
}

export function scoreText(value?: number | null) {
  return typeof value === "number" ? `${value}/100` : "Not scored";
}
