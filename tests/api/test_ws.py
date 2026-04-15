from __future__ import annotations

from fastapi.testclient import TestClient

from high_load_ai.main import app


def test_websocket_stream_smoke() -> None:
    headers = {"X-API-Key": "local-dev-key"}
    with TestClient(app) as client:
        create = client.post("/v1/runs", json={"prompt": "ws"}, headers=headers)
        run_id = create.json()["run_id"]

        with client.websocket_connect(
            f"/v1/runs/{run_id}/ws",
            headers={"X-API-Key": "local-dev-key"},
        ) as websocket:
            first = websocket.receive_json()
            assert "event" in first
