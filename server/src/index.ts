import { createApp } from "./app.js";
import { PlaceStore } from "./store.js";

const port = Number(process.env.PORT ?? 3001);
const store = new PlaceStore();

// Seed a couple of example places so a fresh boot has something to show.
store.create({ name: "Blue Bottle Coffee", category: "cafe", note: "Great pour-over." });
store.create({ name: "Golden Gate Park", category: "park", note: "Sunday strolls." });

const app = createApp(store);

app.listen(port, () => {
  console.log(`[fooplace] API listening on http://localhost:${port}`);
});
