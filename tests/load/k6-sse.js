import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "20s", target: 10 },
    { duration: "40s", target: 30 },
    { duration: "20s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"],
  },
};

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const API_KEY = __ENV.API_KEY || "dev-key";

export default function () {
  const headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Correlation-ID": `k6-${__VU}-${__ITER}`,
  };

  const create = http.post(
    `${BASE}/v1/runs`,
    JSON.stringify({ prompt: "Load test prompt for SSE streaming." }),
    { headers },
  );
  check(create, { "create 200": (r) => r.status === 200 });
  if (create.status !== 200) {
    return;
  }
  const runId = JSON.parse(create.body).run_id;

  const streamHeaders = {
    "X-API-Key": API_KEY,
    "X-Correlation-ID": headers["X-Correlation-ID"],
  };
  const stream = http.get(`${BASE}/v1/runs/${runId}/stream`, {
    headers: streamHeaders,
    timeout: "120s",
  });
  check(stream, { "stream 200": (r) => r.status === 200 });

  sleep(0.5);
}
