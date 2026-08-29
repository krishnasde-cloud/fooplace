import type { SignupPayload } from "./types.ts";

export async function completeSignup(
  token: string,
  payload: SignupPayload,
  signal?: AbortSignal,
): Promise<Record<string, unknown>> {
  const response = await fetch("/api/signup/", {
    method: "POST",
    signal,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body ? String(body.detail) : "";
    throw new Error(
      detail
        ? `Backend returned HTTP ${response.status}: ${detail}`
        : `Backend returned HTTP ${response.status}`,
    );
  }
  return body as Record<string, unknown>;
}
