from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from high_load_ai.main import app


def test_create_run_requires_api_key() -> None:
    with TestClient(app) as client:
        response = client.post("/v1/runs", json={"prompt": "hello"})
    assert response.status_code == 401


def test_create_and_get_run() -> None:
    headers = {"X-API-Key": "local-dev-key"}
    with TestClient(app) as client:
        create = client.post("/v1/runs", json={"prompt": "hello"}, headers=headers)
        assert create.status_code == 200

        run_id = create.json()["run_id"]
        UUID(run_id)

        get = client.get(f"/v1/runs/{run_id}", headers=headers)
        assert get.status_code == 200
        assert get.json()["run_id"] == run_id


def test_sse_stream_endpoint() -> None:
    headers = {"X-API-Key": "local-dev-key"}
    with TestClient(app) as client:
        create = client.post("/v1/runs", json={"prompt": "stream this"}, headers=headers)
        run_id = create.json()["run_id"]

        with client.stream("GET", f"/v1/runs/{run_id}/stream", headers=headers) as response:
            assert response.status_code == 200
            chunks: list[str] = []
            for chunk in response.iter_text():
                if chunk:
                    chunks.append(chunk)
                if len(chunks) >= 3:
                    break

    combined = "".join(chunks)
    assert "event:" in combined
