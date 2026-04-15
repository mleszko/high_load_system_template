from __future__ import annotations

from celery import Celery
from celery.signals import task_postrun, task_prerun

from high_load_ai.core.config import get_settings
from high_load_ai.core.context import set_correlation_id

settings = get_settings()

celery_app = Celery(
    "high_load_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@task_prerun.connect  # type: ignore[untyped-decorator]
def _bind_correlation_id(sender=None, kwargs=None, **_) -> None:  # type: ignore[no-untyped-def]
    if kwargs and (cid := kwargs.get("correlation_id")):
        set_correlation_id(str(cid))
    else:
        set_correlation_id(None)


@task_postrun.connect  # type: ignore[untyped-decorator]
def _clear_correlation_id(sender=None, **_) -> None:  # type: ignore[no-untyped-def]
    set_correlation_id(None)
