from __future__ import annotations

import json
import os
import uuid

from locust import HttpUser, between, task


class RunStreamUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        self.api_key = os.environ.get("LOCUST_API_KEY", "dev-key")

    @task
    def create_and_stream(self) -> None:
        cid = str(uuid.uuid4())
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Correlation-ID": cid,
        }
        with self.client.post(
            "/v1/runs",
            json={"prompt": "Locust load test prompt."},
            headers=headers,
            catch_response=True,
            name="POST /v1/runs",
        ) as post:
            if post.status_code != 200:
                post.failure(f"status {post.status_code}")
                return
            run_id = json.loads(post.text)["run_id"]

        with self.client.get(
            f"/v1/runs/{run_id}/stream",
            headers={"X-API-Key": self.api_key, "X-Correlation-ID": cid},
            stream=True,
            timeout=120,
            catch_response=True,
            name="GET /v1/runs/{id}/stream",
        ) as stream:
            if stream.status_code != 200:
                stream.failure(f"status {stream.status_code}")
                return
            # Read a bounded prefix of the SSE stream
            read = 0
            for _chunk in stream.iter_content(chunk_size=1024):
                read += len(_chunk)
                if read >= 8192:
                    break
