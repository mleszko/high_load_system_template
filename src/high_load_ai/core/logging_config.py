from __future__ import annotations

import logging
import sys

from high_load_ai.core.context import get_correlation_id


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        cid = get_correlation_id()
        record.correlation_id = cid or "-"
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(levelname)s %(name)s [cid=%(correlation_id)s] %(message)s",
        )
    )
    handler.addFilter(CorrelationIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
