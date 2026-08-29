import { describe, expect, it } from "vitest";
import request from "supertest";

import { createApp } from "./app.js";
import { PlaceStore } from "./store.js";

function makeApp() {
  return createApp(new PlaceStore());
}

describe("fooplace API", () => {
  it("reports health", async () => {
    const res = await request(makeApp()).get("/api/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });

  it("starts with an empty place list", async () => {
    const res = await request(makeApp()).get("/api/places");
    expect(res.status).toBe(200);
    expect(res.body.places).toEqual([]);
  });

  it("creates and lists a place", async () => {
    const app = makeApp();
    const created = await request(app)
      .post("/api/places")
      .send({ name: "Dolores Park", category: "park", note: "Sunny days." });
    expect(created.status).toBe(201);
    expect(created.body.place).toMatchObject({
      name: "Dolores Park",
      category: "park",
      note: "Sunny days.",
    });
    expect(created.body.place.id).toBeTruthy();

    const list = await request(app).get("/api/places");
    expect(list.body.places).toHaveLength(1);
    expect(list.body.places[0].name).toBe("Dolores Park");
  });

  it("defaults category to general when omitted", async () => {
    const res = await request(makeApp())
      .post("/api/places")
      .send({ name: "Mystery Spot" });
    expect(res.status).toBe(201);
    expect(res.body.place.category).toBe("general");
  });

  it("rejects a place without a name", async () => {
    const res = await request(makeApp()).post("/api/places").send({ note: "no name" });
    expect(res.status).toBe(400);
    expect(res.body.errors).toEqual(
      expect.arrayContaining([expect.objectContaining({ field: "name" })]),
    );
  });

  it("deletes a place", async () => {
    const app = makeApp();
    const created = await request(app).post("/api/places").send({ name: "Temp" });
    const id = created.body.place.id;

    const del = await request(app).delete(`/api/places/${id}`);
    expect(del.status).toBe(204);

    const missing = await request(app).get(`/api/places/${id}`);
    expect(missing.status).toBe(404);
  });
});
