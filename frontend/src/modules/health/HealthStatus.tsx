import { useEffect, useState } from "react";
import { fetchHealth } from "./api.ts";
import type { HealthResponse } from "./types.ts";
import "./HealthStatus.css";

export function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetchHealth(controller.signal)
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
    <p className={`status ${health ? "ok" : healthError ? "err" : "pending"}`}>
      {health
        ? `API ${health.service}: ${health.status}`
        : healthError
          ? `API unreachable (${healthError}).`
          : "Checking Django API…"}
    </p>
  );
}
