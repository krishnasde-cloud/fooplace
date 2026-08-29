import type { SignupPayload } from "./types.ts";

const KEY = "fooplace.pendingSignup";

export function savePendingSignup(payload: SignupPayload): void {
  sessionStorage.setItem(KEY, JSON.stringify(payload));
}

export function loadPendingSignup(): SignupPayload | null {
  const raw = sessionStorage.getItem(KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as SignupPayload;
  } catch {
    return null;
  }
}

export function clearPendingSignup(): void {
  sessionStorage.removeItem(KEY);
}
