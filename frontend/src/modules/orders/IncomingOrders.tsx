import { useEffect, useState } from "react";
import { confirmOrder, fetchIncoming } from "./api.ts";
import type { SellerOrder } from "./types.ts";
import "../listings/SellerDashboard.css";
import "./IncomingOrders.css";

type IncomingOrdersProps = {
  token: string;
};

function statusLabel(status: SellerOrder["status"]): string {
  if (status === "picked_up") {
    return "Picked up";
  }
  return status.replaceAll("_", " ");
}

function formatWhen(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function remainingLabel(confirmBy: string): string {
  const ms = new Date(confirmBy).getTime() - Date.now();
  if (Number.isNaN(ms) || ms <= 0) {
    return "Confirmation window ended";
  }
  const hours = Math.floor(ms / 3_600_000);
  const minutes = Math.floor((ms % 3_600_000) / 60_000);
  if (hours < 1) {
    return `${minutes} min left to confirm`;
  }
  return `${hours}h ${minutes}m left to confirm`;
}

export function IncomingOrders({ token }: IncomingOrdersProps) {
  const [orders, setOrders] = useState<SellerOrder[]>([]);
  const [hours, setHours] = useState(4);
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  function refresh() {
    return fetchIncoming(token)
      .then((body) => {
        setOrders(body.orders);
        setHours(body.confirm_hours);
        setError(null);
      })
      .catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Could not load orders.");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    void refresh();
  }, [token]);

  async function onConfirm(order: SellerOrder) {
    setBusyId(order.id);
    try {
      await confirmOrder(token, order.id);
      await refresh();
    } catch (confirmError: unknown) {
      setError(confirmError instanceof Error ? confirmError.message : "Could not confirm order.");
    } finally {
      setBusyId(null);
    }
  }

  const pending = orders.filter((order) => order.status === "pending");
  const recent = orders.filter((order) => order.status !== "pending");

  return (
    <section className="listings-page orders-block">
      <div>
        <h1>Incoming orders</h1>
        <p className="listings-lead">
          Confirm a deposit only after you have checked your e-transfer inbox. Unconfirmed
          orders expire after {hours} hours.
        </p>
      </div>
      {error ? <p className="listings-error">{error}</p> : null}
      {loading ? <p className="listings-lead">Loading orders…</p> : null}
      {!loading && pending.length === 0 ? (
        <p className="listings-empty">No orders waiting for confirmation.</p>
      ) : null}
      {pending.map((order) => {
        const ready = Boolean(checked[order.id]);
        return (
          <article key={order.id} className="order-card">
            <div className="order-card-top">
              <span className="listing-status">Awaiting confirmation</span>
              <span className="listing-meta">{remainingLabel(order.confirm_by)}</span>
            </div>
            <h2>{order.dish_name}</h2>
            <p className="listing-meta">
              {order.quantity} × ${Number(order.unit_price).toFixed(2)} · {order.buyer_email}
            </p>
            <p className="listing-meta">Placed {formatWhen(order.created_at)}</p>
            <label className="order-check">
              <input
                type="checkbox"
                checked={ready}
                onChange={(event) =>
                  setChecked((current) => ({
                    ...current,
                    [order.id]: event.target.checked,
                  }))
                }
              />
              I checked my e-transfer inbox and received this deposit
            </label>
            <button
              type="button"
              className="order-confirm"
              disabled={!ready || busyId === order.id}
              onClick={() => void onConfirm(order)}
            >
              {busyId === order.id ? "Confirming…" : "Confirm"}
            </button>
            <OrderHistoryList events={order.history} />
          </article>
        );
      })}
      {recent.length ? (
        <div className="listings-grid">
          <h2 className="listings-lead">Recent orders</h2>
          {recent.map((order) => (
            <article key={order.id} className="order-card muted">
              <span className={`listing-status${order.status === "expired" ? " sold" : ""}`}>
                {statusLabel(order.status)}
              </span>
              <h2>{order.dish_name}</h2>
              <p className="listing-meta">
                {order.quantity} × ${Number(order.unit_price).toFixed(2)} · {order.buyer_email}
              </p>
              <OrderHistoryList events={order.history} />
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function OrderHistoryList({ events }: { events: SellerOrder["history"] }) {
  if (!events.length) {
    return null;
  }
  return (
    <ol className="order-history">
      {events.map((event) => (
        <li key={event.id}>
          {statusLabel(event.status)} · {formatWhen(event.created_at)}
          {event.note ? ` — ${event.note}` : ""}
        </li>
      ))}
    </ol>
  );
}
