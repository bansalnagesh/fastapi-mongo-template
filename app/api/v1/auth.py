# Authentication endpoints

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_user_repo
from app.core.security import get_password_hash, verify_password, create_access_token, refresh_token, JWTBearer
from app.db.repositories.user import UserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
        user_create: UserCreate,
        user_repo: Annotated[UserRepository, Depends(get_user_repo)]
):
    """Register a new user"""
    if user_create.password != user_create.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    # Check if user exists
    existing_user = await user_repo.find_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user_data = user_create.model_dump(exclude={"password", "confirm_password"})
    user_data["hashed_password"] = get_password_hash(user_create.password)

    user = await user_repo.create(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        user_repo: Annotated[UserRepository, Depends(get_user_repo)]
):
    """Login with username and password"""
    user = await user_repo.find_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return create_access_token(str(user.id))


@router.post("/refresh", response_model=Token, dependencies=[Depends(JWTBearer())])
async def refresh(token: str):
    """Refresh access token"""
    return refresh_token(token)


# Optional: Token verification endpoint for testing
@router.get("/verify", dependencies=[Depends(JWTBearer())])
async def verify():
    """Verify access token"""
    return {"status": "valid"}

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
