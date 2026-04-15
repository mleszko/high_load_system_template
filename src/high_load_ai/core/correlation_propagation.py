from __future__ import annotations

from collections.abc import Callable

from fastapi import BackgroundTasks

from high_load_ai.core.context import get_correlation_id, set_correlation_id


def schedule_background_with_correlation(
    background_tasks: BackgroundTasks,
    func: Callable[..., None],
    *args: object,
    **kwargs: object,
) -> None:
    """Run a sync BackgroundTask with the current correlation id restored."""

    cid = get_correlation_id()

    def _runner() -> None:
        set_correlation_id(cid)
        try:
            func(*args, **kwargs)
        finally:
            set_correlation_id(None)

    background_tasks.add_task(_runner)
