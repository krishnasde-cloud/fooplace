import { useEffect, useState } from "react";

import { createPlace, deletePlace, fetchPlaces, type Place } from "./api";

const CATEGORIES = ["general", "cafe", "park", "restaurant", "museum", "bar"];

export function App() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("cafe");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    try {
      setPlaces(await fetchPlaces());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }
    setSubmitting(true);
    try {
      await createPlace({ name, category, note });
      setName("");
      setNote("");
      setError(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save place");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deletePlace(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete place");
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>
          foo<span>place</span>
        </h1>
        <p>Save the spots worth remembering.</p>
      </header>

      <main className="layout">
        <section className="card">
          <h2>Add a place</h2>
          <form onSubmit={handleSubmit} className="form">
            <label>
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Blue Bottle Coffee"
                maxLength={80}
              />
            </label>
            <label>
              Category
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Note
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="What makes it special?"
                rows={3}
              />
            </label>
            <button type="submit" disabled={submitting}>
              {submitting ? "Saving…" : "Save place"}
            </button>
            {error && <p className="error" role="alert">{error}</p>}
          </form>
        </section>

        <section className="card">
          <div className="list-head">
            <h2>Saved places</h2>
            <span className="badge">{places.length}</span>
          </div>
          {loading ? (
            <p className="muted">Loading…</p>
          ) : places.length === 0 ? (
            <p className="muted">No places yet — add your first one.</p>
          ) : (
            <ul className="places">
              {places.map((place) => (
                <li key={place.id} className="place">
                  <div>
                    <p className="place-name">{place.name}</p>
                    <span className={`tag tag-${place.category}`}>{place.category}</span>
                    {place.note && <p className="place-note">{place.note}</p>}
                  </div>
                  <button
                    className="delete"
                    aria-label={`Delete ${place.name}`}
                    onClick={() => handleDelete(place.id)}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
