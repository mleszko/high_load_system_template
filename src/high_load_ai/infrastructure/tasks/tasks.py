from __future__ import annotations

import logging

from high_load_ai.core.context import set_correlation_id
from high_load_ai.infrastructure.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="high_load_ai.finalize_run")  # type: ignore[untyped-decorator]
def finalize_run(run_id: str, correlation_id: str | None = None) -> str:
    if correlation_id:
        set_correlation_id(correlation_id)
    logger.info("finalize_run_task run_id=%s", run_id)
    return f"finalized:{run_id}"
