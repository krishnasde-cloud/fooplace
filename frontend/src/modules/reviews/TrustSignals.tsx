import type { SellerCard } from "./types.ts";
import "./TrustSignals.css";

export function formatJoined(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

export function formatRating(seller: Pick<SellerCard, "average_rating" | "review_count">): string {
  if (seller.average_rating == null) {
    return "No reviews yet";
  }
  return `★ ${seller.average_rating.toFixed(1)} (${seller.review_count})`;
}

type TrustSignalsProps = {
  seller: SellerCard;
  onOpen?: (id: number) => void;
};

export function TrustSignals({ seller, onOpen }: TrustSignalsProps) {
  const body = (
    <>
      <span className="trust-name">{seller.name}</span>
      {seller.neighbourhood ? <span>{seller.neighbourhood}</span> : null}
      <span>{formatRating(seller)}</span>
      {seller.has_food_handler_certification ? (
        <span className="trust-badge">Food handler certified</span>
      ) : null}
    </>
  );
  if (!onOpen) {
    return <p className="trust-row">{body}</p>;
  }
  return (
    <button type="button" className="trust-row link" onClick={() => onOpen(seller.id)}>
      {body}
    </button>
  );
}
