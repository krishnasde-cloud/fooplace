import { useState } from "react";
import { reviewsApi } from "./api.ts";
import type { Review } from "./types.ts";
import "./TrustSignals.css";

type OrderReviewProps = {
  token: string;
  orderId: number;
  existing?: Review | null;
};

export function OrderReview({ token, orderId, existing }: OrderReviewProps) {
  const [review, setReview] = useState<Review | null>(existing ?? null);
  const [stars, setStars] = useState(existing?.stars ?? 0);
  const [comment, setComment] = useState(existing?.comment ?? "");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (review) {
    return (
      <p>
        Your review: {"★".repeat(review.stars)}
        {review.comment ? ` — ${review.comment}` : ""}
      </p>
    );
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (stars < 1) {
          setError("Choose a star rating from 1 to 5.");
          return;
        }
        setPending(true);
        reviewsApi(token)
          .leaveReview(orderId, stars, comment)
          .then((saved) => {
            setReview(saved);
            setError(null);
          })
          .catch((saveError: unknown) => {
            setError(saveError instanceof Error ? saveError.message : "Could not save the review.");
          })
          .finally(() => setPending(false));
      }}
    >
      <p className="listings-lead">How was pickup?</p>
      <div className="trust-stars" aria-label="Star rating">
        {[1, 2, 3, 4, 5].map((value) => (
          <button
            key={value}
            type="button"
            className={stars >= value ? "on" : undefined}
            onClick={() => setStars(value)}
          >
            ★
          </button>
        ))}
      </div>
      <label className="trust-comment">
        Comment (optional)
        <textarea value={comment} onChange={(event) => setComment(event.target.value)} />
      </label>
      {error ? <p className="listings-error">{error}</p> : null}
      <div className="listing-card-actions">
        <button type="submit" disabled={pending}>
          {pending ? "Saving…" : "Leave review"}
        </button>
      </div>
    </form>
  );
}
