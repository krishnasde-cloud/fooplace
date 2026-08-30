import { SignInButton, useAuth } from "@clerk/react";
import { useEffect, useState } from "react";
import { money } from "@/shared/format.ts";
import { fetchOrders } from "./api.ts";
import type { Order } from "./types.ts";
import "./Orders.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

const STATUS_LABEL: Record<Order["status"], string> = {
  pending: "Pending",
  confirmed: "Confirmed",
  ready_for_pickup: "Ready for pickup",
  completed: "Completed",
  expired: "Expired",
  picked_up: "Picked up",
  cancelled: "Cancelled",
};

export function BuyerOrders() {
  if (!publishableKey) {
    return (
      <section className="buyer-orders">
        <h1>My orders</h1>
        <p>Sign in to see your order status.</p>
      </section>
    );
  }
  return <ClerkBuyerOrders />;
}

function ClerkBuyerOrders() {
  const { isSignedIn, getToken } = useAuth();
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSignedIn) {
      return;
    }
    const controller = new AbortController();
    getToken()
      .then((token) => {
        if (!token) {
          throw new Error("Clerk session token missing");
        }
        return fetchOrders(token, controller.signal);
      })
      .then((payload) => {
        setOrders(payload.orders);
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load orders.");
      });
    return () => controller.abort();
  }, [getToken, isSignedIn]);

  return (
    <section className="buyer-orders">
      <h1>My orders</h1>
      {!isSignedIn ? (
        <SignInButton>
          <button type="button" className="order-primary">
            Sign in
          </button>
        </SignInButton>
      ) : null}
      {error ? <p className="order-error">{error}</p> : null}
      {isSignedIn && !orders && !error ? <p>Loading orders…</p> : null}
      {orders && orders.length === 0 ? <p>You have not placed an order yet.</p> : null}
      {orders && orders.length > 0 ? (
        <ul className="order-list">
          {orders.map((order) => (
            <li key={order.id}>
              <a className="order-card" href={`#/orders/${order.id}`}>
                <strong>{order.dish_name}</strong>
                <span>
                  {STATUS_LABEL[order.status]} · {money(order.deposit_amount)} deposit
                </span>
              </a>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
