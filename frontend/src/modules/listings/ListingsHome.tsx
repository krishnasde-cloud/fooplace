import { useAuth } from "@clerk/react";
import { useEffect, useMemo, useState } from "react";
import { Backoffice, SellerHold } from "@/modules/backoffice/index.ts";
import { apiOffice } from "@/modules/backoffice/api.ts";
import { localOffice } from "@/modules/backoffice/local.ts";
import type { SellerReview } from "@/modules/backoffice/index.ts";
import { loadPendingSignup } from "@/modules/signup/pending.ts";
import { apiSource, publicBrowse } from "./api.ts";
import { localSource } from "./local.ts";
import { MarketplaceBrowse } from "./MarketplaceBrowse.tsx";
import { SellerDashboard } from "./SellerDashboard.tsx";
import "@/modules/backoffice/Backoffice.css";

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
  const officeSource = useMemo(() => localOffice(), []);
  const [office, setOffice] = useState(false);
  const seller = loadPendingSignup()?.type === "seller";
  return (
    <>
      <OfficeSwitch office={office} onChange={setOffice} />
      {office ? (
        <Backoffice source={officeSource} />
      ) : seller ? (
        <SellerDashboard source={source} />
      ) : (
        <MarketplaceBrowse source={source} />
      )}
    </>
  );
}

function ClerkListingsHome() {
  const { isSignedIn, getToken } = useAuth();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [token, setToken] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [office, setOffice] = useState(false);
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
  const officeSource = useMemo(() => (token ? apiOffice(token) : null), [token]);
  const isAdmin = me?.type === "admin";
  const review = me?.review;
  const sellerBlocked =
    me?.type === "seller" &&
    Boolean(review && (review.status !== "approved" || review.removed));
  const isSeller = (me?.type === "seller" && !sellerBlocked) || isAdmin;

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

  let body = <MarketplaceBrowse source={source ?? publicSource} />;
  if (isAdmin && office && officeSource) {
    body = <Backoffice source={officeSource} />;
  } else if (sellerBlocked && review?.removed) {
    body = (
      <SellerHold
        title="Seller account removed"
        message="An admin removed this seller account. Contact Fooplace if you think this was a mistake."
      />
    );
  } else if (sellerBlocked && review?.status === "rejected") {
    body = (
      <>
        <SellerHold
          title="Seller application rejected"
          message="An admin reviewed this seller account and did not approve it. You can still browse as a buyer."
        />
        <MarketplaceBrowse source={source ?? publicSource} />
      </>
    );
  } else if (sellerBlocked && review?.status === "pending") {
    body = (
      <SellerHold
        title="Waiting for approval"
        message="Thanks for signing up as a seller. An admin will approve or reject this account before you can publish listings."
      />
    );
  } else if (isSignedIn && isSeller && source) {
    body = <SellerDashboard source={source} />;
  }

  return (
    <>
      {isAdmin ? <OfficeSwitch office={office} onChange={setOffice} /> : null}
      {body}
    </>
  );
}

function OfficeSwitch({
  office,
  onChange,
}: {
  office: boolean;
  onChange: (office: boolean) => void;
}) {
  return (
    <div className="office-switch">
      <button type="button" className={office ? undefined : "active"} onClick={() => onChange(false)}>
        Marketplace
      </button>
      <button type="button" className={office ? "active" : undefined} onClick={() => onChange(true)}>
        Back office
      </button>
    </div>
  );
}
