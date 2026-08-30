import { useEffect, useState } from "react";
import { paths } from "@/app/route.ts";
import { usePublicSeo } from "@/modules/seo/index.ts";
import { readSsrData } from "@/modules/seo/ssrData.ts";
import { formatJoined, formatRating, TrustSignals } from "./TrustSignals.tsx";
import type { ReviewsSource, SellerProfile } from "./types.ts";
import "./TrustSignals.css";

type SellerProfilePageProps = {
  sellerId: number;
  source: Pick<ReviewsSource, "sellerProfile">;
  onBack: () => void;
  indexable?: boolean;
};

export function SellerProfilePage({ sellerId, source, onBack, indexable = true }: SellerProfilePageProps) {
  const [profile, setProfile] = useState<SellerProfile | null>(() => {
    const ssr = readSsrData()?.seller;
    return ssr?.id === sellerId ? ssr : null;
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    source
      .sellerProfile(sellerId)
      .then((payload) => {
        setProfile(payload);
        setError(null);
      })
      .catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Could not load this seller.");
      });
  }, [sellerId, source]);

  usePublicSeo(paths.seller(sellerId), { seller: profile }, indexable && (Boolean(profile) || Boolean(error)));

  return (
    <section className="listings-page">
      <div className="listings-toolbar">
        <div>
          <h1>{profile?.name ?? "Seller"}</h1>
          <p className="listings-lead">Public profile and reviews from completed orders.</p>
        </div>
        <button type="button" className="listings-new" onClick={onBack}>
          Back
        </button>
      </div>
      {error ? <p className="listings-error">{error}</p> : null}
      {profile ? (
        <>
          <TrustSignals seller={profile} />
          <div className="profile-stats">
            <p className="profile-stat">
              <span>Joined</span>
              <strong>{formatJoined(profile.joined_at)}</strong>
            </p>
            <p className="profile-stat">
              <span>Completed orders</span>
              <strong>{profile.completed_orders}</strong>
            </p>
            <p className="profile-stat">
              <span>Rating</span>
              <strong>{formatRating(profile)}</strong>
            </p>
            <p className="profile-stat">
              <span>Neighbourhood</span>
              <strong>{profile.neighbourhood || "—"}</strong>
            </p>
          </div>
          {profile.has_food_handler_certification ? (
            <p className="trust-badge">Food handler certified</p>
          ) : null}
          <h2 className="listings-lead">Reviews</h2>
          {profile.reviews.length === 0 ? (
            <p className="listings-empty">No reviews yet. Buyers can rate a seller after pickup.</p>
          ) : (
            profile.reviews.map((review) => (
              <article key={review.id} className="review-card">
                <strong>
                  {"★".repeat(review.stars)}
                  {"☆".repeat(5 - review.stars)} · {review.buyer_name}
                </strong>
                {review.comment ? <p>{review.comment}</p> : null}
              </article>
            ))
          )}
        </>
      ) : null}
    </section>
  );
}
