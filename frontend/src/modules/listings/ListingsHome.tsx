import { useAuth } from "@clerk/react";
import { BuyerOrders, SellerProfilePage, localReviews, publicSellerProfile, reviewsApi } from "@/modules/reviews/index.ts";
import { loadPendingSignup } from "@/modules/signup/pending.ts";
import { useEffect, useMemo, useState } from "react";
import { apiSource, publicBrowse } from "./api.ts";
import { localSource } from "./local.ts";
import { MarketplaceBrowse } from "./MarketplaceBrowse.tsx";
import { SellerDashboard } from "./SellerDashboard.tsx";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

type MeResponse = {
  id: number;
  type: "buyer" | "seller" | "admin" | "";
};

type Page = { name: "home" } | { name: "profile"; sellerId: number } | { name: "orders" };

export function ListingsHome() {
  if (publishableKey) {
    return <ClerkListingsHome />;
  }
  return <LocalListingsHome />;
}

function LocalListingsHome() {
  const source = useMemo(() => localSource(), []);
  const reviews = useMemo(() => localReviews(), []);
  const publicSource = useMemo(() => ({ listActive: publicBrowse }), []);
  const pending = loadPendingSignup();
  const isSeller = pending?.type === "seller";
  const isBuyer = pending?.type === "buyer";
  const [page, setPage] = useState<Page>({ name: "home" });
  const profileSource = page.name === "profile" && page.sellerId < 0
    ? reviews
    : { sellerProfile: publicSellerProfile };

  if (page.name === "profile") {
    return (
      <SellerProfilePage
        sellerId={Math.abs(page.sellerId)}
        source={profileSource}
        onBack={() => setPage({ name: "home" })}
      />
    );
  }
  if (page.name === "orders") {
    return (
      <BuyerOrders
        source={reviews}
        onBack={() => setPage({ name: "home" })}
        onOpenSeller={(sellerId) => setPage({ name: "profile", sellerId })}
      />
    );
  }
  if (isSeller) {
    return (
      <SellerDashboard
        source={source}
        onPublicProfile={() => setPage({ name: "profile", sellerId: -1 })}
      />
    );
  }
  return (
    <MarketplaceBrowse
      source={publicSource}
      onOpenSeller={(sellerId) => setPage({ name: "profile", sellerId })}
      onOrder={isBuyer ? (listing) => reviews.placeOrder(listing.id) : undefined}
      onOrders={isBuyer ? () => setPage({ name: "orders" }) : undefined}
    />
  );
}

function ClerkListingsHome() {
  const { isSignedIn, getToken } = useAuth();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [token, setToken] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<Page>({ name: "home" });
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
  const reviews = useMemo(
    () => (token ? reviewsApi(token) : { sellerProfile: publicSellerProfile }),
    [token],
  );
  const isSeller = me?.type === "seller" || me?.type === "admin";
  const isBuyer = me?.type === "buyer";

  if (error) {
    return (
      <section className="listings-page">
        <p className="listings-error">{error}</p>
      </section>
    );
  }
  if (isSignedIn && !me) {
    return (
      <section className="listings-page">
        <p className="listings-lead">Loading your listings…</p>
      </section>
    );
  }
  if (page.name === "profile") {
    return (
      <SellerProfilePage
        sellerId={page.sellerId}
        source={reviews}
        onBack={() => setPage({ name: "home" })}
      />
    );
  }
  if (page.name === "orders" && token) {
    return (
      <BuyerOrders
        source={reviewsApi(token)}
        onBack={() => setPage({ name: "home" })}
        onOpenSeller={(sellerId) => setPage({ name: "profile", sellerId })}
      />
    );
  }
  if (isSignedIn && isSeller && source) {
    return (
      <SellerDashboard
        source={source}
        onPublicProfile={
          me?.id ? () => setPage({ name: "profile", sellerId: me.id }) : undefined
        }
      />
    );
  }
  return (
    <MarketplaceBrowse
      source={source ?? publicSource}
      onOpenSeller={(sellerId) => setPage({ name: "profile", sellerId })}
      onOrder={
        isBuyer && token
          ? (listing) => reviewsApi(token).placeOrder(listing.id)
          : undefined
      }
      onOrders={isBuyer ? () => setPage({ name: "orders" }) : undefined}
    />
  );
}
