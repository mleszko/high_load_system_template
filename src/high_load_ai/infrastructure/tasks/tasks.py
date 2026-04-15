from __future__ import annotations

from high_load_ai.infrastructure.tasks.celery_app import celery_app


@celery_app.task(name="high_load_ai.finalize_run")  # type: ignore[untyped-decorator]
def finalize_run(run_id: str) -> str:
    # Placeholder for heavy post-processing that should not block API responses.
    return f"finalized:{run_id}"
