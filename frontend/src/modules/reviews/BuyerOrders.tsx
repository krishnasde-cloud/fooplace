import { useEffect, useState } from "react";
import { TrustSignals } from "./TrustSignals.tsx";
import type { BuyerOrder, ReviewsSource } from "./types.ts";
import "./TrustSignals.css";

type BuyerOrdersProps = {
  source: ReviewsSource;
  onOpenSeller: (id: number) => void;
  onBack: () => void;
};

export function BuyerOrders({ source, onOpenSeller, onBack }: BuyerOrdersProps) {
  const [orders, setOrders] = useState<BuyerOrder[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [stars, setStars] = useState<Record<number, number>>({});
  const [comments, setComments] = useState<Record<number, string>>({});

  function refresh() {
    return source
      .myOrders()
      .then((items) => {
        setOrders(items);
        setError(null);
      })
      .catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Could not load orders.");
      });
  }

  useEffect(() => {
    void refresh();
  }, [source]);

  return (
    <section className="listings-page">
      <div className="listings-toolbar">
        <div>
          <h1>Your orders</h1>
          <p className="listings-lead">Mark pickup complete, then leave a star rating.</p>
        </div>
        <button type="button" className="listings-new" onClick={onBack}>
          Browse
        </button>
      </div>
      {error ? <p className="listings-error">{error}</p> : null}
      {orders.length === 0 ? (
        <p className="listings-empty">No orders yet. Reserve a dish from the marketplace.</p>
      ) : null}
      {orders.map((order) => (
        <article key={order.id} className="review-card">
          <strong>
            {order.dish_name} × {order.quantity}
          </strong>
          <p className="listings-lead">Status: {order.status.replaceAll("_", " ")}</p>
          <TrustSignals seller={order.seller} onOpen={onOpenSeller} />
          {order.status !== "picked_up" && order.status !== "cancelled" ? (
            <div className="listing-card-actions">
              <button
                type="button"
                onClick={() => {
                  void source
                    .completeOrder(order.id)
                    .then(() => refresh())
                    .catch((completeError: unknown) => {
                      setError(
                        completeError instanceof Error
                          ? completeError.message
                          : "Could not complete this order.",
                      );
                    });
                }}
              >
                Mark picked up
              </button>
            </div>
          ) : null}
          {order.status === "picked_up" && !order.review ? (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                const rating = stars[order.id] ?? 0;
                if (rating < 1) {
                  setError("Choose a star rating from 1 to 5.");
                  return;
                }
                void source
                  .leaveReview(order.id, rating, comments[order.id] ?? "")
                  .then(() => refresh())
                  .catch((reviewError: unknown) => {
                    setError(
                      reviewError instanceof Error ? reviewError.message : "Could not save the review.",
                    );
                  });
              }}
            >
              <div className="trust-stars" aria-label="Star rating">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={(stars[order.id] ?? 0) >= value ? "on" : undefined}
                    onClick={() => setStars((current) => ({ ...current, [order.id]: value }))}
                  >
                    ★
                  </button>
                ))}
              </div>
              <label className="trust-comment">
                Comment (optional)
                <textarea
                  value={comments[order.id] ?? ""}
                  onChange={(event) =>
                    setComments((current) => ({ ...current, [order.id]: event.target.value }))
                  }
                />
              </label>
              <div className="listing-card-actions">
                <button type="submit">Leave review</button>
              </div>
            </form>
          ) : null}
          {order.review ? (
            <p>
              Your review: {"★".repeat(order.review.stars)}
              {order.review.comment ? ` — ${order.review.comment}` : ""}
            </p>
          ) : null}
        </article>
      ))}
    </section>
  );
}
