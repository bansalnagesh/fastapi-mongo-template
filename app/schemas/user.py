from typing import Optional, List

from pydantic import BaseModel, EmailStr

from .base import BaseSchema


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_superuser: bool = False
    roles: List[str] = ["user"]


class UserCreate(UserBase):
    password: str
    confirm_password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserInDB(UserBase, BaseSchema):
    hashed_password: str
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None


class UserResponse(UserBase, BaseSchema):
    pass
