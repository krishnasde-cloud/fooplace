import { useEffect } from "react";
import { isPublicRoute, type Route } from "@/app/route.ts";
import { applyDocumentSeo, type SeoDocument } from "./head.ts";

export function PageSeo({ route }: { route: Route }) {
  useEffect(() => {
    if (isPublicRoute(route) && route.page !== "seller") {
      return;
    }
    if (route.page === "seller" && route.id !== "local") {
      return;
    }
    const doc: SeoDocument = {
      title: "Fooplace",
      description: "Fooplace home-cooked marketplace.",
      robots: "noindex, nofollow",
      canonical: `${window.location.origin}${window.location.pathname}`,
      jsonLd: null,
    };
    applyDocumentSeo(doc);
  }, [route]);
  return null;
}
