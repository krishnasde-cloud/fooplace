import { useAuth } from "@clerk/react";
import { useEffect, useState } from "react";

type MeResponse = {
  user_id: string;
  session_id: string | null;
};

export function ClerkSessionStatus() {
  const { isSignedIn, getToken } = useAuth();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [meError, setMeError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSignedIn) {
      setMe(null);
      setMeError(null);
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
        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }
        return (await response.json()) as MeResponse;
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
        ? `Signed in as ${me.user_id}`
        : meError
          ? `Django rejected the Clerk session (${meError}).`
          : "Checking Clerk session with Django…"}
    </p>
  );
}
