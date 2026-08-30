import { useEffect, useState } from "react";

export type Route =
  | { page: "browse" }
  | { page: "listing"; id: number }
  | { page: "sell" }
  | { page: "orders" }
  | { page: "order"; id: number }
  | { page: "seller"; id: number | "local" };

export const paths = {
  browse: "/",
  listing: (id: number) => `/listings/${id}/`,
  seller: (id: number | "local") => `/sellers/${id}/`,
  sell: "/sell",
  orders: "/orders",
  order: (id: number) => `/orders/${id}/`,
};

export function parsePath(path: string): Route {
  const normalized = path.replace(/^#/, "") || "/";
  const listing = normalized.match(/^\/listings\/(\d+)\/?$/);
  if (listing) {
    return { page: "listing", id: Number(listing[1]) };
  }
  const seller = normalized.match(/^\/sellers\/(\d+|local)\/?$/);
  if (seller) {
    return { page: "seller", id: seller[1] === "local" ? "local" : Number(seller[1]) };
  }
  const order = normalized.match(/^\/orders\/(\d+)\/?$/);
  if (order) {
    return { page: "order", id: Number(order[1]) };
  }
  if (normalized === "/orders" || normalized === "/orders/") {
    return { page: "orders" };
  }
  if (normalized === "/sell" || normalized === "/sell/") {
    return { page: "sell" };
  }
  return { page: "browse" };
}

export function isPublicRoute(route: Route): boolean {
  return route.page === "browse" || route.page === "listing" || route.page === "seller";
}

function currentPath(): string {
  if (window.location.hash.startsWith("#/")) {
    return window.location.hash.slice(1).split("?")[0] || "/";
  }
  return window.location.pathname || "/";
}

export function useRoute(): Route {
  const [path, setPath] = useState(currentPath);
  useEffect(() => {
    if (window.location.hash.startsWith("#/")) {
      window.history.replaceState(null, "", window.location.hash.slice(1));
    }
    const onPop = () => setPath(currentPath());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);
  return parsePath(path);
}
