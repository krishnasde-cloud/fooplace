import cors from "cors";
import express, { type Express } from "express";

import { PlaceStore, validateNewPlace } from "./store.js";

export function createApp(store: PlaceStore = new PlaceStore()): Express {
  const app = express();
  app.use(cors());
  app.use(express.json());

  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", uptime: process.uptime() });
  });

  app.get("/api/places", (_req, res) => {
    res.json({ places: store.list() });
  });

  app.get("/api/places/:id", (req, res) => {
    const place = store.get(req.params.id);
    if (!place) {
      res.status(404).json({ error: "Place not found." });
      return;
    }
    res.json({ place });
  });

  app.post("/api/places", (req, res) => {
    const errors = validateNewPlace(req.body);
    if (errors.length > 0) {
      res.status(400).json({ errors });
      return;
    }
    const place = store.create(req.body);
    res.status(201).json({ place });
  });

  app.delete("/api/places/:id", (req, res) => {
    const removed = store.remove(req.params.id);
    if (!removed) {
      res.status(404).json({ error: "Place not found." });
      return;
    }
    res.status(204).end();
  });

  return app;
}
