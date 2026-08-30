import { useEffect, useId, useState } from "react";
import { autocompleteAddress } from "./api.ts";
import type { Place } from "./types.ts";
import "./PickupAddressField.css";

type PickupAddressFieldProps = {
  value: string;
  onChange: (value: string) => void;
};

export function PickupAddressField({ value, onChange }: PickupAddressFieldProps) {
  const listId = useId();
  const [suggestions, setSuggestions] = useState<Place[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const text = value.trim();
    if (text.length < 3) {
      setSuggestions([]);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      autocompleteAddress(text, controller.signal)
        .then((results) => {
          setSuggestions(results);
          setOpen(results.length > 0);
        })
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") {
            return;
          }
          setSuggestions([]);
        });
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [value]);

  return (
    <label className="signup-field pickup-address">
      Pickup address
      <input
        type="text"
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(suggestions.length > 0)}
        onBlur={() => window.setTimeout(() => setOpen(false), 120)}
        placeholder="Start typing a street address"
        autoComplete="off"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        required
      />
      {open && suggestions.length > 0 ? (
        <ul id={listId} className="pickup-suggestions" role="listbox">
          {suggestions.map((place) => (
            <li key={`${place.lat},${place.lon},${place.formatted}`}>
              <button
                type="button"
                role="option"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  onChange(place.formatted);
                  setSuggestions([]);
                  setOpen(false);
                }}
              >
                {place.formatted}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </label>
  );
}
