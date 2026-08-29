import { useEffect, useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "./assets/vite.svg";
import { AuthHeader } from "./AuthHeader.tsx";
import { ClerkSessionStatus } from "./ClerkSessionStatus.tsx";
import "./App.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

type HealthResponse = {
  status: string;
  service: string;
};

function App() {
  const [count, setCount] = useState(0);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/health/", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }
        return (await response.json()) as HealthResponse;
      })
      .then((payload) => {
        setHealth(payload);
        setHealthError(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setHealthError(error instanceof Error ? error.message : "Unknown error");
      });

    return () => controller.abort();
  }, []);

  return (
    <>
      <AuthHeader />
      <section id="center">
        <div className="hero">
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div>
          <h1>Fooplace</h1>
          <p>React frontend talking to the Django backend.</p>
        </div>
        <p className={`status ${health ? "ok" : healthError ? "err" : "pending"}`}>
          {health
            ? `API ${health.service}: ${health.status}`
            : healthError
              ? `API unreachable (${healthError}).`
              : "Checking Django API…"}
        </p>
        {publishableKey ? <ClerkSessionStatus /> : null}
        <button
          type="button"
          className="counter"
          onClick={() => setCount((value) => value + 1)}
        >
          Count is {count}
        </button>
      </section>
    </>
  );
}

export default App;
