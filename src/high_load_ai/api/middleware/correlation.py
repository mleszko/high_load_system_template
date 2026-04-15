from __future__ import annotations

import uuid
from typing import cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from high_load_ai.core.context import set_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    header_name = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        incoming = request.headers.get(self.header_name)
        correlation_id = incoming.strip() if incoming else str(uuid.uuid4())
        set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id

        response = cast(Response, await call_next(request))
        response.headers[self.header_name] = correlation_id
        return response
