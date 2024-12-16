import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

import logging

logger = logging.getLogger("api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def set_body(self, request: Request):
        receive_ = await request._receive()

        async def receive() -> Message:
            return receive_

        request._receive = receive

    async def dispatch(
            self, request: Request, call_next: Callable
    ) -> Response:
        # Start timer
        start_time = time.time()

        # Get request body
        await self.set_body(request)
        body = await request.body()

        # Prepare request logging
        request_id = request.headers.get("X-Request-ID", "")

        # Log request
        logger.info(
            "Request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "",
                "headers": dict(request.headers),
                "body": body.decode() if body else ""
            }
        )

        # Process request and get response
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            "Response",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration": f"{duration:.3f}s",
                "headers": dict(response.headers)
            }
        )

        return response
