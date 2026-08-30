import { useState } from "react";
import type { Listing, ListingInput } from "./types.ts";
import "./ListingForm.css";

type ListingFormProps = {
  initial?: Listing | null;
  submitLabel: string;
  onSubmit: (input: ListingInput) => Promise<void> | void;
  onCancel: () => void;
};

function tomorrow(): string {
  const day = new Date();
  day.setDate(day.getDate() + 1);
  return day.toISOString().slice(0, 10);
}

function clockValue(value: string | undefined, fallback: string): string {
  return value ? value.slice(0, 5) : fallback;
}

async function readPhoto(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("Could not read that photo."));
    reader.readAsDataURL(file);
  });
}

export function ListingForm({ initial, submitLabel, onSubmit, onCancel }: ListingFormProps) {
  const [photo, setPhoto] = useState(initial?.photo ?? "");
  const [dishName, setDishName] = useState(initial?.dish_name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [price, setPrice] = useState(initial ? Number(initial.price).toFixed(2) : "");
  const [quantity, setQuantity] = useState(initial ? String(initial.quantity_available) : "1");
  const [neighbourhood, setNeighbourhood] = useState(initial?.neighbourhood ?? "");
  const [pickupDate, setPickupDate] = useState(initial?.pickup_date ?? tomorrow());
  const [windowStart, setWindowStart] = useState(clockValue(initial?.pickup_window_start, "17:00"));
  const [windowEnd, setWindowEnd] = useState(clockValue(initial?.pickup_window_end, "19:00"));
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function buildInput(): ListingInput | null {
    if (!photo) {
      setError("Add a photo of the dish.");
      return null;
    }
    if (!dishName.trim() || !description.trim() || !neighbourhood.trim()) {
      setError("Dish name, description, and neighbourhood are required.");
      return null;
    }
    if (/^\d+\s+\S+/.test(neighbourhood.trim())) {
      setError("Use a neighbourhood, not a street address. The exact address is shared after an order is confirmed.");
      return null;
    }
    const amount = Number(price);
    const count = Number(quantity);
    if (!Number.isFinite(amount) || amount <= 0 || !Number.isInteger(count) || count < 0) {
      setError("Enter a price and how many portions are available.");
      return null;
    }
    return {
      photo,
      dish_name: dishName.trim(),
      description: description.trim(),
      price: amount.toFixed(2),
      quantity_available: count,
      neighbourhood: neighbourhood.trim(),
      pickup_date: pickupDate,
      pickup_window_start: windowStart,
      pickup_window_end: windowEnd,
    };
  }

  return (
    <form
      className="listing-form"
      onSubmit={(event) => {
        event.preventDefault();
        const input = buildInput();
        if (!input) {
          return;
        }
        setError(null);
        setPending(true);
        Promise.resolve(onSubmit(input))
          .catch((submitError: unknown) => {
            setError(submitError instanceof Error ? submitError.message : "Could not save listing.");
          })
          .finally(() => setPending(false));
      }}
    >
      <h1>{initial ? "Edit listing" : "New listing"}</h1>
      <p>Buyers see the neighbourhood and pickup window — not your street address.</p>

      <label>
        Photo
        <input
          type="file"
          accept="image/*"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (!file) {
              return;
            }
            readPhoto(file)
              .then((dataUrl) => {
                setPhoto(dataUrl);
                setError(null);
              })
              .catch((readError: unknown) => {
                setError(readError instanceof Error ? readError.message : "Could not read that photo.");
              });
          }}
        />
      </label>
      {photo ? <img className="listing-photo-preview" src={photo} alt="Dish preview" /> : null}

      <label>
        Dish name
        <input value={dishName} onChange={(event) => setDishName(event.target.value)} required />
      </label>
      <label>
        Description
        <textarea value={description} onChange={(event) => setDescription(event.target.value)} required />
      </label>
      <div className="listing-row">
        <label>
          Price
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
            required
          />
        </label>
        <label>
          Quantity available
          <input
            type="number"
            min="0"
            step="1"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            required
          />
        </label>
      </div>
      <label>
        Pickup neighbourhood
        <input
          value={neighbourhood}
          onChange={(event) => setNeighbourhood(event.target.value)}
          placeholder="e.g. Kensington"
          required
        />
        <span className="listing-hint">Neighbourhood only — exact address waits until an order is confirmed.</span>
      </label>
      <label>
        Pickup date
        <input
          type="date"
          value={pickupDate}
          onChange={(event) => setPickupDate(event.target.value)}
          required
        />
      </label>
      <div className="listing-row">
        <label>
          Window start
          <input
            type="time"
            value={windowStart}
            onChange={(event) => setWindowStart(event.target.value)}
            required
          />
        </label>
        <label>
          Window end
          <input type="time" value={windowEnd} onChange={(event) => setWindowEnd(event.target.value)} required />
        </label>
      </div>

      {error ? <p className="listing-error">{error}</p> : null}

      <div className="listing-actions">
        <button type="submit" className="listing-submit" disabled={pending}>
          {pending ? "Saving…" : submitLabel}
        </button>
        <button type="button" className="listing-cancel" onClick={onCancel} disabled={pending}>
          Cancel
        </button>
      </div>
    </form>
  );
}
