# app/api/deps.py
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from app.core.security import JWTBearer, verify_token
from app.db.repositories.user import UserRepository
from app.models.user import User


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