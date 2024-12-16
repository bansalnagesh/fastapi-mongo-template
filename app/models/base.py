# app/models/base.py
from datetime import datetime
import uuid
from typing import Any, Dict
from pydantic import BaseModel, Field, ConfigDict


def generate_uuid() -> str:
    """Generate a new UUID4 without dashes"""
    return str(uuid.uuid4()).replace('-', '')


def datetime_to_milliseconds(dt: datetime) -> int:
    """Convert datetime to milliseconds timestamp"""
    return int(dt.timestamp() * 1000)


def milliseconds_to_datetime(ms: int) -> datetime:
    """Convert milliseconds timestamp to datetime"""
    return datetime.fromtimestamp(ms / 1000)


class MongoBaseModel(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: datetime_to_milliseconds}
    )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to convert timestamps to milliseconds for DB storage"""
        data = super().model_dump(**kwargs)

        # Convert datetime fields to milliseconds for DB storage
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = datetime_to_milliseconds(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            data['updated_at'] = datetime_to_milliseconds(data['updated_at'])

        return data

    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'MongoBaseModel':
        """Create model instance from DB data, converting milliseconds to datetime"""
        if data:
            if 'created_at' in data and isinstance(data['created_at'], (int, float)):
                data['created_at'] = milliseconds_to_datetime(int(data['created_at']))
            if 'updated_at' in data and isinstance(data['updated_at'], (int, float)):
                data['updated_at'] = milliseconds_to_datetime(int(data['updated_at']))
        return cls(**data)