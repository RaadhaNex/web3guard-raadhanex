export const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

type ApiOptions = {
  headers?: HeadersInit;
};

function buildApiUrl(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  return `${API_BASE}${cleanPath}`;
}

function readableErrorDetail(value: unknown): string {
  if (!value) return "Unknown API error";

  if (typeof value === "string") return value;

  if (Array.isArray(value)) {
    return value
      .map((item) => readableErrorDetail(item))
      .filter(Boolean)
      .join(" | ");
  }

  if (typeof value === "object") {
    const record = value as Record<string, unknown>;

    if (typeof record.message === "string") return record.message;
    if (typeof record.error === "string") return record.error;
    if (typeof record.detail === "string") return record.detail;
    if (typeof record.msg === "string") return record.msg;

    if (record.detail) {
      return readableErrorDetail(record.detail);
    }

    const loc = Array.isArray(record.loc) ? record.loc.join(".") : "";
    const msg = typeof record.msg === "string" ? record.msg : "";
    const type = typeof record.type === "string" ? record.type : "";

    if (loc || msg || type) {
      return [loc, msg, type].filter(Boolean).join(": ");
    }

    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  return String(value);
}

async function readResponse(response: Response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

function mergeHeaders(
  baseHeaders: Record<string, string>,
  extraHeaders?: HeadersInit
): HeadersInit {
  if (!extraHeaders) return baseHeaders;

  if (extraHeaders instanceof Headers) {
    const merged = new Headers(baseHeaders);
    extraHeaders.forEach((value, key) => merged.set(key, value));
    return merged;
  }

  if (Array.isArray(extraHeaders)) {
    return [...Object.entries(baseHeaders), ...extraHeaders];
  }

  return {
    ...baseHeaders,
    ...extraHeaders,
  };
}

async function requestApi<T>(
  method: "GET" | "POST" | "PATCH" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
  options: ApiOptions = {}
): Promise<T> {
  const headers =
    body === undefined
      ? mergeHeaders({}, options.headers)
      : mergeHeaders({ "Content-Type": "application/json" }, options.headers);

  const response = await fetch(buildApiUrl(path), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  const data = await readResponse(response);

  if (!response.ok) {
    const message = readableErrorDetail(data);

    throw new Error(
      `API ${response.status} ${response.statusText}: ${message}`
    );
  }

  return data as T;
}

export function apiGet<T>(path: string, options?: ApiOptions) {
  return requestApi<T>("GET", path, undefined, options);
}

export function apiPost<T>(path: string, body?: unknown, options?: ApiOptions) {
  return requestApi<T>("POST", path, body, options);
}

export function apiPatch<T>(path: string, body?: unknown, options?: ApiOptions) {
  return requestApi<T>("PATCH", path, body, options);
}

export function apiPut<T>(path: string, body?: unknown, options?: ApiOptions) {
  return requestApi<T>("PUT", path, body, options);
}

export function apiDelete<T>(path: string, options?: ApiOptions) {
  return requestApi<T>("DELETE", path, undefined, options);
}

export async function apiGetText(path: string, options: ApiOptions = {}) {
  const response = await fetch(buildApiUrl(path), {
    method: "GET",
    headers: mergeHeaders({}, options.headers),
  });

  const text = await response.text();

  if (!response.ok) {
    throw new Error(
      `API ${response.status} ${response.statusText}: ${
        text || "Request failed"
      }`
    );
  }

  return text;
}