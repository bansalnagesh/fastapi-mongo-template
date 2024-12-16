# User specific database operations

from typing import Optional
from app.models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User, "users")

    async def find_by_email(self, email: str) -> Optional[User]:
        return await self.find_one({"email": email})

    async def find_by_oauth(self, provider: str, oauth_id: str) -> Optional[User]:
        return await self.find_one({
            "oauth_provider": provider,
            "oauth_id": oauth_id
        })