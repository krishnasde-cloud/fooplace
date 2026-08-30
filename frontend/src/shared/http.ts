export async function parseApi<T>(response: Response): Promise<T> {
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
  return body as T;
}

export async function apiGet<T>(
  path: string,
  token?: string | null,
  signal?: AbortSignal,
): Promise<T> {
  const headers: HeadersInit = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(path, { signal, headers });
  return parseApi<T>(response);
}

export async function apiSend<T>(
  path: string,
  token: string,
  method: "POST",
  body?: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, {
    method,
    signal,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body ?? {}),
  });
  return parseApi<T>(response);
}
