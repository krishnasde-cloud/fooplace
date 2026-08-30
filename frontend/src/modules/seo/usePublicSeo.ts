import { useEffect } from "react";
import type { Listing } from "@/modules/listings/types.ts";
import type { SellerProfile } from "@/modules/reviews/types.ts";
import { applyDocumentSeo, seoForPublicPath } from "./head.ts";

export function usePublicSeo(
  path: string,
  data: { listings?: Listing[]; listing?: Listing | null; seller?: SellerProfile | null },
  enabled = true,
) {
  const listingId = data.listing?.id ?? null;
  const sellerId = data.seller?.id ?? null;
  const listingCount = data.listings?.length ?? 0;
  useEffect(() => {
    if (!enabled) {
      return;
    }
    applyDocumentSeo(seoForPublicPath(path, window.location.origin, data));
  }, [path, listingId, sellerId, listingCount, data, enabled]);
}
