# Authentication service
from datetime import timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.oauth import verify_google_token
from app.db.repositories.user import UserRepository
from app.schemas.token import Token
from app.models.user import User
from typing import Annotated
from fastapi import Depends
from app.api.deps import get_user_repo


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)]
) -> "AuthService":
    return AuthService(user_repo)


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.user_repo.find_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_token(self, user: User) -> Token:
        access_token = create_access_token(
            user.id,
            roles=user.roles
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600  # 1 hour
        )

    async def register_user(self, email: str, password: str, full_name: Optional[str] = None) -> User:
        # Check if user exists
        existing_user = await self.user_repo.find_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        user_data = {
            "email": email,
            "hashed_password": get_password_hash(password),
            "full_name": full_name,
        }

        user = await self.user_repo.create(user_data)
        return user

    async def authenticate_google_user(self, token: str) -> Tuple[User, Token]:
        try:
            # Verify Google token
            google_data = await verify_google_token(token)

            # Check if user exists
            user = await self.user_repo.find_by_oauth("google", google_data["sub"])

            if not user:
                # Create new user from Google data
                user_data = {
                    "email": google_data["email"],
                    "full_name": google_data.get("name"),
                    "oauth_provider": "google",
                    "oauth_id": google_data["sub"],
                    "hashed_password": get_password_hash(token)  # Use token as password
                }
                user = await self.user_repo.create(user_data)

            # Create access token
            token = await self.create_token(user)

            return user, token

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
