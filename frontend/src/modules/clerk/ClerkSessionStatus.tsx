import { useAuth } from "@clerk/react";
import { useEffect, useState } from "react";

type MeResponse = {
  user_id: string;
  email: string;
  connected_using: string;
  type: "buyer" | "seller" | "admin";
  is_active: boolean;
  is_verified: boolean;
  first_logged_in: string;
  last_logged_in: string;
  session_id: string | null;
};

export function ClerkSessionStatus() {
  const { isSignedIn, getToken } = useAuth();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [meError, setMeError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSignedIn) {
      return;
    }

    const controller = new AbortController();

    getToken()
      .then((token) => {
        if (!token) {
          throw new Error("Clerk session token missing");
        }
        return fetch("/api/me/", {
          signal: controller.signal,
          headers: { Authorization: `Bearer ${token}` },
        });
      })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            payload && typeof payload === "object" && "detail" in payload
              ? String(payload.detail)
              : "";
          throw new Error(
            detail
              ? `Backend returned HTTP ${response.status}: ${detail}`
              : `Backend returned HTTP ${response.status}`,
          );
        }
        return payload as MeResponse;
      })
      .then((payload) => {
        setMe(payload);
        setMeError(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setMeError(error instanceof Error ? error.message : "Unknown error");
      });

    return () => controller.abort();
  }, [getToken, isSignedIn]);

  if (!isSignedIn) {
    return <p className="status">Sign in with Clerk to call the Django API.</p>;
  }

  return (
    <p className={`status ${me ? "ok" : meError ? "err" : "pending"}`}>
      {me
        ? `Signed in as ${me.email || me.user_id} (${me.type})`
        : meError
          ? `Django rejected the Clerk session (${meError}).`
          : "Checking Clerk session with Django…"}
    </p>
  );
}
