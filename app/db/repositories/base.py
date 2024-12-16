# app/db/repositories/base.py
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.mongodb import db
from app.models.base import MongoBaseModel, datetime_to_milliseconds, generate_uuid

ModelType = TypeVar("ModelType", bound=MongoBaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], collection_name: str):
        self.model = model
        self.collection_name = collection_name

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return db.db[self.collection_name]

    async def find_one(self, query: Dict) -> Optional[ModelType]:
        """Find single document and convert to model"""
        doc = await self.collection.find_one(query)
        if doc:
            return self.model.from_db(doc)
        return None

    async def find_by_id(self, id: str) -> Optional[ModelType]:
        """Find document by ID"""
        return await self.find_one({"_id": id})

    async def find_many(
            self,
            query: Dict,
            skip: int = 0,
            limit: int = 100,
            sort: List[tuple] = None
    ) -> List[ModelType]:
        """Find multiple documents"""
        cursor = self.collection.find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        docs = await cursor.to_list(length=limit)
        return [self.model.from_db(doc) for doc in docs]

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Create new document"""
        # Ensure we have an ID
        if "_id" not in data:
            data["_id"] = generate_uuid()

        # Add timestamps if not present
        current_time = datetime_to_milliseconds(datetime.utcnow())
        if "created_at" not in data:
            data["created_at"] = current_time
        if "updated_at" not in data:
            data["updated_at"] = current_time

        # Create model instance
        doc = self.model(**data)

        # Get dict representation
        db_data = doc.model_dump(by_alias=True)

        # Insert into DB
        await self.collection.insert_one(db_data)

        # Return the created document
        return await self.find_by_id(db_data["_id"])

    async def update(
            self,
            query: Dict,
            data: Dict[str, Any],
            upsert: bool = False
    ) -> Optional[ModelType]:
        """Update document(s)"""
        # Always update the updated_at timestamp
        update_data = {
            "$set": {
                **data,
                "updated_at": datetime_to_milliseconds(datetime.utcnow())
            }
        }

        result = await self.collection.update_one(
            query, update_data, upsert=upsert
        )

        if result.modified_count > 0 or (upsert and result.upserted_id):
            return await self.find_one(query)
        return None

    async def update_by_id(
            self,
            id: str,
            data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update document by ID"""
        return await self.update({"_id": id}, data)

    async def delete(self, query: Dict) -> bool:
        """Delete document(s)"""
        result = await self.collection.delete_one(query)
        return result.deleted_count > 0

    async def delete_by_id(self, id: str) -> bool:
        """Delete document by ID"""
        return await self.delete({"_id": id})