import { randomUUID } from "node:crypto";

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

export interface ValidationError {
  field: string;
  message: string;
}

/**
 * In-memory place store. Kept intentionally simple so the environment can be
 * exercised end-to-end without provisioning an external database.
 */
export class PlaceStore {
  private places: Place[] = [];

  list(): Place[] {
    return [...this.places].sort((a, b) =>
      b.createdAt.localeCompare(a.createdAt),
    );
  }

  get(id: string): Place | undefined {
    return this.places.find((place) => place.id === id);
  }

  create(input: NewPlace): Place {
    const place: Place = {
      id: randomUUID(),
      name: input.name.trim(),
      category: (input.category ?? "general").trim() || "general",
      note: (input.note ?? "").trim(),
      createdAt: new Date().toISOString(),
    };
    this.places.push(place);
    return place;
  }

  remove(id: string): boolean {
    const before = this.places.length;
    this.places = this.places.filter((place) => place.id !== id);
    return this.places.length < before;
  }

  reset(): void {
    this.places = [];
  }
}

export function validateNewPlace(body: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (typeof body !== "object" || body === null) {
    return [{ field: "body", message: "Request body must be a JSON object." }];
  }
  const record = body as Record<string, unknown>;
  if (typeof record.name !== "string" || record.name.trim().length === 0) {
    errors.push({ field: "name", message: "Name is required." });
  } else if (record.name.trim().length > 80) {
    errors.push({ field: "name", message: "Name must be 80 characters or fewer." });
  }
  if (record.category !== undefined && typeof record.category !== "string") {
    errors.push({ field: "category", message: "Category must be a string." });
  }
  if (record.note !== undefined && typeof record.note !== "string") {
    errors.push({ field: "note", message: "Note must be a string." });
  }
  return errors;
}
