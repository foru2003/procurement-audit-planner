"use client";

import { useState } from "react";

export default function Home() {
  const [result, setResult] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function probe() {
    setBusy(true);
    try {
      const res = await fetch("/api/probe", { cache: "no-store" });
      const text = await res.text();
      setResult(`HTTP ${res.status}\n${text}`);
    } catch (err) {
      setResult(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Procurement Audit Planner: deploy skeleton</h1>
      <p>
        Checks that the Python function can read the bundled data file, skill script, agent
        prompt, and run the Part A quote verifier on the precomputed PDF text.
      </p>
      <button onClick={probe} disabled={busy}>
        {busy ? "Running…" : "Run Python probe"}
      </button>
      <pre style={{ background: "#f4f4f4", padding: "1rem", overflow: "auto" }}>{result}</pre>
    </main>
  );
}
