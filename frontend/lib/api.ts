export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiPost<T>(path: string, payload: unknown, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    body: JSON.stringify(payload),
    ...init,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data as T;
}

export async function apiPatch<T>(path: string, payload: unknown, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    body: JSON.stringify(payload),
    ...init,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data as T;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data as T;
}

export async function apiGetText(path: string, init?: RequestInit): Promise<string> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  const data = await response.text();
  if (!response.ok) {
    throw new Error(data || "Request failed");
  }
  return data;
}

export function buildUpiLink(amount: number, packageName: string, reference = "preview"): string | null {
  if (amount <= 0) return null;
  const pa = encodeURIComponent(process.env.NEXT_PUBLIC_UPI_ID || "raadhanex@upi");
  const pn = encodeURIComponent(process.env.NEXT_PUBLIC_UPI_NAME || "RAADHANEX");
  const tn = encodeURIComponent(`Web3Guard AI ${packageName} ${reference}`);
  return `upi://pay?pa=${pa}&pn=${pn}&am=${amount}&cu=INR&tn=${tn}`;
}
