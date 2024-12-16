# app/models/user.py
from typing import Optional, List

from app.models.base import MongoBaseModel


class User(MongoBaseModel):
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    is_superuser: bool = False
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    roles: List[str] = ["user"]

    class Config:
        collection_name = "users"  # MongoDB collection name


# Example document in MongoDB:
"""
{
    "_id": "550e8400e29b41d4a716446655440000",  # UUID4 without dashes
    "email": "user@example.com",
    "hashed_password": "...",
    "full_name": "John Doe",
    "is_superuser": false,
    "oauth_provider": null,
    "oauth_id": null,
    "roles": ["user"],
    "created_at": 1634567890123,  # Milliseconds timestamp
    "updated_at": 1634567890123,  # Milliseconds timestamp
    "is_active": true
}
"""
