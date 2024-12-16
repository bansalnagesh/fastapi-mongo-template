# Authentication endpoints

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService, get_auth_service
from app.db.repositories.user import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
        user_create: UserCreate,
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """Register a new user."""
    if user_create.password != user_create.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    user = await auth_service.register_user(
        email=user_create.email,
        password=user_create.password,
        full_name=user_create.full_name
    )
    return user


# @router.post("/login", response_model=Token)
# async def login(
#         form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
#         auth_service: Annotated[AuthService, Depends()]
# ):
#     """Login with username and password."""
#     user = await auth_service.authenticate_user(
#         form_data.username,
#         form_data.password
#     )
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     return await auth_service.create_token(user)


# @router.post("/google", response_model=Token)
# async def google_auth(
#         token: str,
#         auth_service: Annotated[AuthService, Depends()]
# ):
#     """Authenticate with Google OAuth."""
#     try:
#         _, token = await auth_service.authenticate_google_user(token)
#         return token
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=str(e)
#         )