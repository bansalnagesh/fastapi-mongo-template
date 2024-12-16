# app/schemas/token.py
from typing import List

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    user_id: str
    exp: int
    iat: int
    type: str = "access_token"
    roles: List[str] = ["user"]


class TokenRefreshRequest(BaseModel):
    token: str
