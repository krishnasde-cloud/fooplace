import { useState } from "react";
import { HealthStatus } from "@/modules/health/index.ts";
import reactLogo from "../assets/react.svg";
import viteLogo from "../assets/vite.svg";
import "./App.css";

function App() {
  const [count, setCount] = useState(0);

  return (
    <section id="center">
      <div className="hero">
        <img src={reactLogo} className="framework" alt="React logo" />
        <img src={viteLogo} className="vite" alt="Vite logo" />
      </div>
      <div>
        <h1>Fooplace</h1>
        <p>React frontend talking to the Django backend.</p>
      </div>
      <HealthStatus />
      <button
        type="button"
        className="counter"
        onClick={() => setCount((value) => value + 1)}
      >
        Count is {count}
      </button>
    </section>
  );
}

export default App;
