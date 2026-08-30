import { renderToString } from "react-dom/server";
import type { Listing } from "@/modules/listings/types.ts";
import type { SellerProfile } from "@/modules/reviews/types.ts";
import { headMarkup, seoForPublicPath } from "./head.ts";
import { PublicBrowse, PublicListing, PublicMissing, PublicSeller } from "./PublicMarkup.tsx";
import { listingIdFromPath, sellerIdFromPath } from "./publicPath.ts";

export type PublicSsrData = {
  listings?: Listing[];
  listing?: Listing | null;
  seller?: SellerProfile | null;
};

export function renderPublicPage(path: string, origin: string, data: PublicSsrData) {
  const seo = seoForPublicPath(path, origin, data);
  const listingId = listingIdFromPath(path);
  const sellerId = sellerIdFromPath(path);
  let body: string;
  if (listingId !== null) {
    body = data.listing
      ? renderToString(<PublicListing listing={data.listing} />)
      : renderToString(<PublicMissing message="This listing is not available." />);
  } else if (sellerId !== null) {
    body = data.seller
      ? renderToString(<PublicSeller seller={data.seller} />)
      : renderToString(<PublicMissing message="This seller is not available." />);
  } else {
    body = renderToString(<PublicBrowse listings={data.listings ?? []} />);
  }
  return {
    status: seo.robots === "index, follow" ? 200 : 404,
    head: headMarkup(seo),
    body,
    robots: seo.robots,
    title: seo.title,
  };
}
