import { useAuth } from "@clerk/react";
import { useEffect, useMemo, useState } from "react";
import { loadPendingSignup } from "@/modules/signup/pending.ts";
import { apiSource, publicBrowse } from "./api.ts";
import { localSource } from "./local.ts";
import { MarketplaceBrowse } from "./MarketplaceBrowse.tsx";
import { SellerDashboard } from "./SellerDashboard.tsx";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

type MeResponse = {
  type: "buyer" | "seller" | "admin" | "";
};

export function ListingsHome() {
  if (publishableKey) {
    return <ClerkListingsHome />;
  }
  return <LocalListingsHome />;
}

function LocalListingsHome() {
  const source = useMemo(() => localSource(), []);
  const seller = loadPendingSignup()?.type === "seller";
  if (seller) {
    return <SellerDashboard source={source} />;
  }
  return <MarketplaceBrowse source={source} />;
}

function ClerkListingsHome() {
  const { isSignedIn, getToken } = useAuth();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [token, setToken] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const publicSource = useMemo(
    () => ({
      listActive: publicBrowse,
    }),
    [],
  );

  useEffect(() => {
    if (!isSignedIn) {
      setMe(null);
      setToken("");
      return;
    }
    const controller = new AbortController();
    getToken()
      .then(async (sessionToken) => {
        if (!sessionToken) {
          throw new Error("Clerk session token missing");
        }
        const response = await fetch("/api/me/", {
          signal: controller.signal,
          headers: { Authorization: `Bearer ${sessionToken}` },
        });
        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }
        const payload = (await response.json()) as MeResponse;
        setToken(sessionToken);
        setMe(payload);
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load your account.");
      });
    return () => controller.abort();
  }, [getToken, isSignedIn]);

  const source = useMemo(() => (token ? apiSource(token) : null), [token]);
  const isSeller = me?.type === "seller" || me?.type === "admin";

  if (error) {
    return (
      <section className="listings-page">
        <p className="listings-error">{error}</p>
      </section>
    );
  }
  if (isSignedIn && isSeller && source) {
    return <SellerDashboard source={source} />;
  }
  if (isSignedIn && !me) {
    return (
      <section className="listings-page">
        <p className="listings-lead">Loading your listings…</p>
      </section>
    );
  }
  return <MarketplaceBrowse source={source ?? publicSource} />;
}
