import type { HealthResponse } from "./types.ts";

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch("/api/health/", { signal });
  if (!response.ok) {
    throw new Error(`Backend returned HTTP ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}
