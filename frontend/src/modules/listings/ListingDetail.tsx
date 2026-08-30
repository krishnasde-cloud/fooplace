import { useEffect, useState } from "react";
import { paths } from "@/app/route.ts";
import { PlaceOrder } from "@/modules/orders/PlaceOrder.tsx";
import { PublicListing, usePublicSeo } from "@/modules/seo/index.ts";
import { readSsrData } from "@/modules/seo/ssrData.ts";
import { fetchListing } from "./api.ts";
import type { Listing } from "./types.ts";
import "./ListingDetail.css";

export function ListingDetail({ id }: { id: number }) {
  const [listing, setListing] = useState<Listing | null>(() => {
    const ssr = readSsrData()?.listing;
    return ssr?.id === id ? ssr : null;
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchListing(id, controller.signal)
      .then((payload) => {
        setListing(payload);
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load listing.");
      });
    return () => controller.abort();
  }, [id]);

  usePublicSeo(paths.listing(id), { listing }, Boolean(listing) || Boolean(error));

  if (error) {
    return (
      <section className="listing-detail">
        <a className="listing-back" href={paths.browse}>
          ← Browse listings
        </a>
        <p className="listing-status">{error}</p>
      </section>
    );
  }
  if (!listing) {
    return (
      <section className="listing-detail">
        <p>Loading listing…</p>
      </section>
    );
  }

  return (
    <PublicListing listing={listing}>
      <PlaceOrder listing={listing} />
    </PublicListing>
  );
}
