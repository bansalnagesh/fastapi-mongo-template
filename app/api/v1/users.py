# User management endpoints
# app/api/v1/users.py
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_active_user, get_current_superuser, get_user_repo
from app.core.security import get_password_hash, JWTBearer
from app.db.repositories.user import UserRepository
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(JWTBearer())]  # Global protection for all routes
)


@router.get("/me", response_model=UserResponse)
async def read_current_user(
        current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
        update_data: UserUpdate,
        current_user: Annotated[User, Depends(get_current_active_user)],
        user_repo: Annotated[UserRepository, Depends(get_user_repo)]
):
    """Update current user information."""
    update_dict = update_data.model_dump(exclude_unset=True)

    if "password" in update_dict:
        update_dict["hashed_password"] = get_password_hash(update_dict.pop("password"))

    updated_user = await user_repo.update_by_id(current_user.id, update_dict)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )

    return updated_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
        current_user: Annotated[User, Depends(get_current_active_user)],
        user_repo: Annotated[UserRepository, Depends()]
):
    """
    Delete current user account.
    """
    success = await user_repo.delete_by_id(current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )


# Admin routes
@router.get("", response_model=List[UserResponse])
async def list_users(
        *,
        skip: int = 0,
        limit: int = 100,
        current_user: Annotated[User, Depends(get_current_superuser)],
        user_repo: Annotated[UserRepository, Depends()]
):
    """
    List all users. Only accessible by superusers.
    """
    users = await user_repo.find_many({}, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
        user_id: str,
        current_user: Annotated[User, Depends(get_current_superuser)],
        user_repo: Annotated[UserRepository, Depends()]
):
    """
    Get user by ID. Only accessible by superusers.
    """
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
        user_id: str,
        update_data: UserUpdate,
        current_user: Annotated[User, Depends(get_current_superuser)],
        user_repo: Annotated[UserRepository, Depends()]
):
    """
    Update user by ID. Only accessible by superusers.
    """
    # Check if user exists
    existing_user = await user_repo.find_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prepare update data
    update_dict = update_data.model_dump(exclude_unset=True)

    # Hash password if it's being updated
    if "password" in update_dict:
        update_dict["hashed_password"] = get_password_hash(update_dict.pop("password"))

    # Update user
    updated_user = await user_repo.update_by_id(user_id, update_dict)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )

    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_id: str,
        current_user: Annotated[User, Depends(get_current_superuser)],
        user_repo: Annotated[UserRepository, Depends()]
):
    """
    Delete user by ID. Only accessible by superusers.
    """
    success = await user_repo.delete_by_id(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
