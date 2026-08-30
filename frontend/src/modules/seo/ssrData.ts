import type { Listing } from "@/modules/listings/types.ts";
import type { SellerProfile } from "@/modules/reviews/types.ts";

export type PublicSsrData = {
  listings?: Listing[];
  listing?: Listing | null;
  seller?: SellerProfile | null;
};

export function readSsrData(): PublicSsrData | null {
  if (typeof document === "undefined") {
    return null;
  }
  const node = document.getElementById("fooplace-ssr-data");
  if (!node?.textContent) {
    return null;
  }
  try {
    return JSON.parse(node.textContent) as PublicSsrData;
  } catch {
    return null;
  }
}

export function ssrDataScript(data: PublicSsrData): string {
  return `<script type="application/json" id="fooplace-ssr-data">${JSON.stringify(data).replaceAll("<", "\\u003c")}</script>`;
}
