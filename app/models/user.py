from typing import Optional, List

from .base import MongoBaseModel


class User(MongoBaseModel):
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    is_superuser: bool = False
    oauth_provider: Optional[str] = None  # "google", etc.
    oauth_id: Optional[str] = None
    roles: List[str] = ["user"]
