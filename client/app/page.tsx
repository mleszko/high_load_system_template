"use client";

import { useMemo, useState } from "react";

const defaultApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function HomePage() {
  const [apiUrl, setApiUrl] = useState(defaultApiUrl);
  const [apiKey, setApiKey] = useState("dev-key");
  const [prompt, setPrompt] = useState("Summarize why async APIs improve tail latency under high load.");
  const [runId, setRunId] = useState("");
  const [status, setStatus] = useState("idle");
  const [events, setEvents] = useState<string[]>([]);

  const canStart = useMemo(() => prompt.trim().length > 0 && apiKey.trim().length > 0, [prompt, apiKey]);

  async function createRun() {
    if (!canStart) return;
    setStatus("creating");
    setEvents([]);

    const response = await fetch(`${apiUrl}/v1/runs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      setStatus(`create_failed:${response.status}`);
      return;
    }

    const payload = (await response.json()) as { run_id: string };
    setRunId(payload.run_id);
    setStatus("created");
  }

  function streamRun() {
    if (!runId) return;
    setStatus("streaming");

    const source = new EventSource(`/api/stream-proxy?run_id=${encodeURIComponent(runId)}&api_key=${encodeURIComponent(apiKey)}`);

    source.addEventListener("progress", (event) => {
      setEvents((prev) => [...prev, `progress: ${event.data}`]);
    });

    source.addEventListener("token", (event) => {
      setEvents((prev) => [...prev, `token: ${event.data}`]);
    });

    source.addEventListener("done", (event) => {
      setEvents((prev) => [...prev, `done: ${event.data}`]);
      setStatus("done");
      source.close();
    });

    source.addEventListener("error", () => {
      setEvents((prev) => [...prev, "error: stream disconnected"]);
      setStatus("error");
      source.close();
    });
  }

  return (
    <main style={{ maxWidth: 980, margin: "32px auto", fontFamily: "Arial, sans-serif" }}>
      <h1>High Load AI Stream Demo</h1>
      <p>Start a run, then stream SSE progress and token events from the FastAPI service.</p>

      <section style={{ display: "grid", gap: 12, marginTop: 20 }}>
        <label>
          API URL
          <input value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} style={{ width: "100%" }} />
        </label>

        <label>
          API Key
          <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: "100%" }} />
        </label>

        <label>
          Prompt
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={5}
            style={{ width: "100%" }}
          />
        </label>

        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={createRun} disabled={!canStart}>Create run</button>
          <button onClick={streamRun} disabled={!runId}>Start stream</button>
        </div>

        <div>Run ID: {runId || "(none)"}</div>
        <div>Status: {status}</div>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Stream events</h2>
        <pre style={{ background: "#111", color: "#ddd", padding: 12, minHeight: 240, overflow: "auto" }}>
          {events.join("\n") || "(no events yet)"}
        </pre>
      </section>
    </main>
  );
}
