import time
from typing import Dict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app,
            requests_limit: int = 100,  # Number of requests
            window_size: int = 60  # Time window in seconds
    ):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_size = window_size
        self.requests: Dict[str, list] = {}  # IP -> list of timestamps

    def _clean_old_requests(self, client_ip: str, current_time: float):
        """Remove requests older than window_size"""
        if client_ip in self.requests:
            self.requests[client_ip] = [
                timestamp
                for timestamp in self.requests[client_ip]
                if current_time - timestamp < self.window_size
            ]

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(client_ip, current_time)

        # Initialize requests list for new clients
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        # Process request
        response = await call_next(request)
        return response
