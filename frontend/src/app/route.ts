import { useEffect, useState } from "react";

export type Route =
  | { page: "browse" }
  | { page: "listing"; id: number }
  | { page: "sell" }
  | { page: "orders" }
  | { page: "order"; id: number }
  | { page: "signup" };

export function parseHash(hash: string): Route {
  const path = hash.replace(/^#/, "") || "/";
  const listing = path.match(/^\/listings\/(\d+)\/?$/);
  if (listing) {
    return { page: "listing", id: Number(listing[1]) };
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
  if (path === "/signup" || path === "/signup/") {
    return { page: "signup" };
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
