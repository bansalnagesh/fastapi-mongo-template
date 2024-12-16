# app/api/deps.py
import time
from typing import Annotated, Generator

from cachetools import TTLCache
from fastapi import Depends, status
from fastapi import Request, HTTPException

from app.core.security import JWTBearer, verify_token
from app.db.repositories.user import UserRepository
from app.models.user import User


class RateLimiter:
    def __init__(
            self,
            requests_limit: int = 3,  # Number of requests allowed
            window_size: int = 60  # Time window in seconds
    ):
        self.cache = TTLCache(maxsize=10000, ttl=window_size)
        self.requests_limit = requests_limit
        self.window_size = window_size

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Get request timestamps for this IP
        request_times = self.cache.get(client_ip, [])

        # Clean old requests
        request_times = [
            timestamp
            for timestamp in request_times
            if current_time - timestamp < self.window_size
        ]

        # Check rate limit
        if len(request_times) >= self.requests_limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Too many requests",
                    "retry_after": int(self.window_size - (current_time - request_times[0]))
                }
            )

        # Add current request
        request_times.append(current_time)
        self.cache[client_ip] = request_times


# Rate limiters for different endpoints
auth_rate_limiter = RateLimiter(requests_limit=5, window_size=60)  # 5 requests per minute
api_rate_limiter = RateLimiter(requests_limit=100, window_size=60)  # 100 requests per minute


def get_user_repo() -> Generator[UserRepository, None, None]:
    repo = UserRepository()
    try:
        yield repo
    finally:
        # Clean up if needed
        pass


async def get_current_user(
        token: Annotated[str, Depends(JWTBearer())],
        user_repo: Annotated[UserRepository, Depends(get_user_repo)]
) -> User:
    """Get current user from JWT token"""
    try:
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )

        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation error: {str(e)}"
        )

    user = await user_repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Check if current user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
        current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Check if current user is superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user
