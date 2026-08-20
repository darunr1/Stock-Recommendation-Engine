import type { ApiError } from "./types";

export function readCookie(name: string): string | undefined {
  if (typeof document === "undefined") return undefined;
  return document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${name}=`))
    ?.split("=")
    .slice(1)
    .join("=");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const csrf = readCookie("csrf_token");
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(csrf && !["GET", "HEAD"].includes(method)
        ? { "X-CSRF-Token": csrf }
        : {}),
      ...init.headers,
    },
  });
  const data = (await response.json().catch(() => ({}))) as T & ApiError;
  if (!response.ok) {
    throw new Error(
      data.error?.message ?? "The request could not be completed.",
    );
  }
  return data;
}

export async function serverApi<T>(path: string): Promise<T | null> {
  const upstream = process.env.API_UPSTREAM_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${upstream}/api/v1${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    return response.ok ? ((await response.json()) as T) : null;
  } catch {
    return null;
  }
}
