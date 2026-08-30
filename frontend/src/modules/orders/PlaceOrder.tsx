import { SignInButton, useAuth } from "@clerk/react";
import { useState } from "react";
import type { Listing } from "@/modules/listings/types.ts";
import { depositDue, money } from "@/shared/format.ts";
import { placeOrder } from "./api.ts";
import "./Orders.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

export function PlaceOrder({ listing }: { listing: Listing }) {
  if (publishableKey) {
    return <ClerkPlaceOrder listing={listing} />;
  }
  return <SignedOutOrder listing={listing} />;
}

function SignedOutOrder({ listing }: { listing: Listing }) {
  const pickupEnded = new Date(listing.pickup_end) <= new Date();
  const unavailable = listing.sold_out || listing.quantity_available < 1 || pickupEnded;
  return (
    <section className="place-order">
      <h2>Place an order</h2>
      <DepositPreview listing={listing} quantity={1} />
      {unavailable ? (
        <p>This listing is not available to order.</p>
      ) : (
        <p>Sign in to reserve a portion and send the deposit by e-transfer.</p>
      )}
    </section>
  );
}

function ClerkPlaceOrder({ listing }: { listing: Listing }) {
  const { isSignedIn, getToken } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pickupEnded = new Date(listing.pickup_end) <= new Date();
  const unavailable = listing.sold_out || listing.quantity_available < 1 || pickupEnded;
  const maxQuantity = Math.max(listing.quantity_available, 1);

  async function submit() {
    setError(null);
    setPending(true);
    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Clerk session token missing");
      }
      const order = await placeOrder(token, listing.id, quantity);
      window.location.hash = `#/orders/${order.id}`;
    } catch (submitError: unknown) {
      setError(submitError instanceof Error ? submitError.message : "Could not place order.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="place-order">
      <h2>Place an order</h2>
      <label className="quantity-row">
        Quantity
        <input
          type="number"
          min={1}
          max={maxQuantity}
          value={quantity}
          disabled={unavailable}
          onChange={(event) => setQuantity(Number(event.target.value) || 1)}
        />
      </label>
      <DepositPreview listing={listing} quantity={quantity} />
      {error ? <p className="order-error">{error}</p> : null}
      {unavailable ? <p>This listing is not available to order.</p> : null}
      {!unavailable && isSignedIn ? (
        <div className="order-actions">
          <button type="button" className="order-primary" disabled={pending} onClick={submit}>
            {pending ? "Placing order…" : "Place order"}
          </button>
        </div>
      ) : null}
      {!unavailable && !isSignedIn ? (
        <SignInButton>
          <button type="button" className="order-primary">
            Sign in to order
          </button>
        </SignInButton>
      ) : null}
    </section>
  );
}

function DepositPreview({ listing, quantity }: { listing: Listing; quantity: number }) {
  const safeQuantity = Math.max(1, quantity);
  return (
    <div className="deposit-box">
      <p>
        Total {money(Number(listing.price) * safeQuantity)} · deposit due (50%){" "}
        <strong>{depositDue(listing.price, safeQuantity)}</strong>
      </p>
      <p>After you place the order you will see the seller’s e-transfer email.</p>
    </div>
  );
}
