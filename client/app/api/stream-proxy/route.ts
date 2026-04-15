import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const runId = request.nextUrl.searchParams.get("run_id");
  const apiKey = request.nextUrl.searchParams.get("api_key");

  if (!runId || !apiKey) {
    return new Response("run_id and api_key are required", { status: 400 });
  }

  const upstream = await fetch(`${apiUrl}/v1/runs/${runId}/stream`, {
    headers: { "X-API-Key": apiKey },
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(`Upstream error: ${upstream.status}`, { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
