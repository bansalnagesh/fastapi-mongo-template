# app/models/base.py
from datetime import datetime
from typing import Any, Dict
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict

class MongoBaseModel(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB format"""
        data = self.model_dump(by_alias=True, exclude_none=True)
        # Convert string id to ObjectId
        if "_id" in data:
            data["_id"] = ObjectId(data["_id"])
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "MongoBaseModel":
        """Create model instance from MongoDB data"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)