import { useEffect, useState } from "react";

export type Route =
  | { page: "browse" }
  | { page: "listing"; id: number }
  | { page: "sell" }
  | { page: "orders" }
  | { page: "order"; id: number }
  | { page: "seller"; id: number | "local" };

export function parseHash(hash: string): Route {
  const path = hash.replace(/^#/, "") || "/";
  const listing = path.match(/^\/listings\/(\d+)\/?$/);
  if (listing) {
    return { page: "listing", id: Number(listing[1]) };
  }
  const seller = path.match(/^\/sellers\/(\d+|local)\/?$/);
  if (seller) {
    return { page: "seller", id: seller[1] === "local" ? "local" : Number(seller[1]) };
  }
  const order = path.match(/^\/orders\/(\d+)\/?$/);
  if (order) {
    return { page: "order", id: Number(order[1]) };
  }
  if (path === "/orders" || path === "/orders/") {
    return { page: "orders" };
  }
  if (path === "/sell" || path === "/sell/") {
    return { page: "sell" };
  }
  return { page: "browse" };
}

export function useHashRoute(): Route {
  const [hash, setHash] = useState(() => window.location.hash);
  useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return parseHash(hash);
}
