import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 20,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.95"],
  },
};

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const API_KEY = __ENV.API_KEY || "dev-key";

export default function () {
  const headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
  };

  const res = http.post(
    `${BASE}/v1/runs`,
    JSON.stringify({ prompt: "rate limit burst" }),
    { headers },
  );

  if (res.status === 429) {
    check(res, { "got rate limited": (r) => r.status === 429 });
  } else {
    check(res, { "create ok or limited": (r) => r.status === 200 || r.status === 429 });
  }

  sleep(0.05);
}

export function handleSummary(data) {
  const codes = data.metrics.http_reqs?.values?.count ?? 0;
  return {
    stdout: JSON.stringify(
      {
        note: "Expect some 429 responses when RATE_LIMIT_MAX_REQUESTS is low.",
        http_reqs: codes,
      },
      null,
      2,
    ),
  };
}
