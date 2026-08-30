import { useAuth } from "@clerk/react";
import { useEffect, useState } from "react";
import { OrderReview } from "@/modules/reviews/index.ts";
import { money, pickupWindow } from "@/shared/format.ts";
import { fetchOrder, markDepositSent, markPickedUp } from "./api.ts";
import { ORDER_STEPS, type Order, type OrderStatus } from "./types.ts";
import "./Orders.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

export function OrderStatus({ id }: { id: number }) {
  if (!publishableKey) {
    return (
      <section className="order-status">
        <a className="listing-back" href="#/orders">
          ← My orders
        </a>
        <p>Sign in to view this order.</p>
      </section>
    );
  }
  return <ClerkOrderStatus id={id} />;
}

function ClerkOrderStatus({ id }: { id: number }) {
  const { isSignedIn, getToken } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

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
        setToken(token);
        return fetchOrder(token, id, controller.signal);
      })
      .then((payload) => {
        setOrder(payload);
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load order.");
      });
    return () => controller.abort();
  }, [getToken, id, isSignedIn]);

  async function run(action: (token: string) => Promise<Order>) {
    setPending(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Clerk session token missing");
      }
      setOrder(await action(token));
    } catch (actionError: unknown) {
      setError(actionError instanceof Error ? actionError.message : "Update failed.");
    } finally {
      setPending(false);
    }
  }

  if (!isSignedIn) {
    return (
      <section className="order-status">
        <p>Sign in to view this order.</p>
      </section>
    );
  }

  return (
    <section className="order-status">
      <a className="listing-back" href="#/orders">
        ← My orders
      </a>
      {error ? <p className="order-error">{error}</p> : null}
      {!order && !error ? <p>Loading order…</p> : null}
      {order ? (
        <>
          <h1>{order.dish_name}</h1>
          <StatusTimeline status={order.status} />
          <div className="deposit-box">
            <p>
              Quantity {order.quantity} · total {money(order.total)}
            </p>
            <p>
              Deposit owed (50%): <strong>{money(order.deposit_amount)}</strong>
            </p>
            <p>
              Send e-transfer to <strong>{order.seller_etransfer_email}</strong> ({order.seller_name})
            </p>
            <p>Pickup in {order.neighbourhood}</p>
            <p>{pickupWindow(order.pickup_start, order.pickup_end)}</p>
          </div>
          <div className="order-actions">
            {order.status === "pending" ? (
              <button
                type="button"
                className="order-primary"
                disabled={pending}
                onClick={() => run((token) => markDepositSent(token, order.id))}
              >
                {pending ? "Saving…" : "I sent the deposit"}
              </button>
            ) : null}
            {order.status === "ready_for_pickup" ? (
              <button
                type="button"
                className="order-primary"
                disabled={pending}
                onClick={() => run((token) => markPickedUp(token, order.id))}
              >
                {pending ? "Saving…" : "I picked this up"}
              </button>
            ) : null}
          </div>
          {(order.status === "completed" || order.status === "picked_up") && token ? (
            <OrderReview token={token} orderId={order.id} />
          ) : null}
          {order.seller_id ? (
            <p>
              <a href={`#/sellers/${order.seller_id}`}>View seller profile</a>
            </p>
          ) : null}
        </>
      ) : null}
    </section>
  );
}

function StatusTimeline({ status }: { status: OrderStatus }) {
  if (status === "expired") {
    return (
      <ol className="order-timeline">
        <li className="current">Expired</li>
      </ol>
    );
  }
  const currentIndex = ORDER_STEPS.findIndex((step) => step.id === status);
  return (
    <ol className="order-timeline">
      {ORDER_STEPS.map((step, index) => (
        <li
          key={step.id}
          className={index < currentIndex ? "done" : index === currentIndex ? "current" : undefined}
        >
          {step.label}
        </li>
      ))}
    </ol>
  );
}
