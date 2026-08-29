export interface Place {
  id: string;
  name: string;
  category: string;
  note: string;
  createdAt: string;
}

export interface NewPlace {
  name: string;
  category?: string;
  note?: string;
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  return text ? (JSON.parse(text) as T) : ({} as T);
}

export async function fetchPlaces(): Promise<Place[]> {
  const res = await fetch("/api/places");
  if (!res.ok) throw new Error(`Failed to load places (${res.status})`);
  const data = await parseJson<{ places: Place[] }>(res);
  return data.places;
}

export async function createPlace(input: NewPlace): Promise<Place> {
  const res = await fetch("/api/places", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const data = await parseJson<{ errors?: { message: string }[] }>(res);
    const message = data.errors?.map((e) => e.message).join(" ") ?? `Request failed (${res.status})`;
    throw new Error(message);
  }
  const data = await parseJson<{ place: Place }>(res);
  return data.place;
}

export async function deletePlace(id: string): Promise<void> {
  const res = await fetch(`/api/places/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete place (${res.status})`);
}
