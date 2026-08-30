import { useEffect, useState } from "react";
import { fetchNotifications } from "./api.ts";
import type { BuyerNotice } from "./types.ts";
import "./IncomingOrders.css";

type BuyerNotificationsProps = {
  token: string;
};

export function BuyerNotifications({ token }: BuyerNotificationsProps) {
  const [notices, setNotices] = useState<BuyerNotice[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchNotifications(token)
      .then((items) => {
        if (!controller.signal.aborted) {
          setNotices(items);
          setError(null);
        }
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load notifications.");
      });
    return () => controller.abort();
  }, [token]);

  if (error) {
    return (
      <section className="listings-page orders-block">
        <p className="listings-error">{error}</p>
      </section>
    );
  }
  if (!notices.length) {
    return null;
  }

  return (
    <section className="listings-page orders-block">
      <h1>Order updates</h1>
      {notices.map((notice) => (
        <article key={notice.id} className="order-card">
          <span className={`listing-status${notice.kind === "expired" ? " sold" : ""}`}>
            {notice.kind === "expired" ? "Expired" : "Confirmed"}
          </span>
          <p className="listing-meta">{notice.message}</p>
        </article>
      ))}
    </section>
  );
}
