import { useAuth } from "@clerk/react";
import { useEffect, useMemo, useState } from "react";
import { SellerHold } from "@/modules/backoffice/index.ts";
import type { SellerReview } from "@/modules/backoffice/index.ts";
import { loadPendingSignup } from "@/modules/signup/pending.ts";
import { BuyerNotifications, IncomingOrders } from "@/modules/orders/index.ts";
import { apiOrderSource, localSource as localOrders } from "@/modules/orders/local.ts";
import { apiSource, publicBrowse } from "./api.ts";
import { localSource } from "./local.ts";
import { MarketplaceBrowse } from "./MarketplaceBrowse.tsx";
import { SellerDashboard } from "./SellerDashboard.tsx";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

type MeResponse = {
  type: "buyer" | "seller" | "admin" | "";
  review: SellerReview | null;
};

export function ListingsHome() {
  if (publishableKey) {
    return <ClerkListingsHome />;
  }
  return <LocalListingsHome />;
}

function LocalListingsHome() {
  const source = useMemo(() => localSource(), []);
  const orders = useMemo(() => localOrders(), []);
  const seller = loadPendingSignup()?.type === "seller";
  if (seller) {
    return (
      <>
        <IncomingOrders source={orders} />
        <SellerDashboard source={source} />
      </>
    );
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
  const orderSource = useMemo(() => apiOrderSource(token), [token]);
  const review = me?.review;
  const sellerBlocked =
    me?.type === "seller" &&
    Boolean(review && (review.status !== "approved" || review.removed));
  const isSeller = (me?.type === "seller" && !sellerBlocked) || me?.type === "admin";

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
  if (sellerBlocked && review?.removed) {
    return (
      <SellerHold
        title="Seller account removed"
        message="An admin removed this seller account. Contact Fooplace if you think this was a mistake."
      />
    );
  }
  if (sellerBlocked && review?.status === "rejected") {
    return (
      <>
        <SellerHold
          title="Seller application rejected"
          message="An admin reviewed this seller account and did not approve it. You can still browse as a buyer."
        />
        {token ? <BuyerNotifications token={token} /> : null}
        <MarketplaceBrowse source={source ?? publicSource} />
      </>
    );
  }
  if (sellerBlocked && review?.status === "pending") {
    return (
      <SellerHold
        title="Waiting for approval"
        message="Thanks for signing up as a seller. An admin will approve or reject this account before you can publish listings."
      />
    );
  }
  if (isSignedIn && isSeller && source) {
    return (
      <>
        <IncomingOrders source={orderSource} />
        <SellerDashboard source={source} />
      </>
    );
  }
  return (
    <>
      {token ? <BuyerNotifications token={token} /> : null}
      <MarketplaceBrowse source={source ?? publicSource} />
    </>
  );
}
