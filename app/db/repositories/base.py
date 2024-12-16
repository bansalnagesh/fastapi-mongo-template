# app/db/repositories/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from bson import ObjectId
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.mongodb import db
from app.models.base import MongoBaseModel

ModelType = TypeVar("ModelType", bound=MongoBaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], collection_name: str):
        self.model = model
        self.collection_name = collection_name

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return db.db[self.collection_name]

    async def find_one(self, query: Dict) -> Optional[ModelType]:
        doc = await self.collection.find_one(query)
        if doc:
            return self.model.from_mongo(doc)
        return None

    async def find_by_id(self, id: Union[str, ObjectId]) -> Optional[ModelType]:
        if isinstance(id, str):
            id = ObjectId(id)
        return await self.find_one({"_id": id})

    async def find_many(
            self,
            query: Dict,
            skip: int = 0,
            limit: int = 100,
            sort: List[tuple] = None
    ) -> List[ModelType]:
        cursor = self.collection.find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        docs = await cursor.to_list(length=limit)
        return [self.model.from_mongo(doc) for doc in docs]

    async def create(self, data: Dict[str, Any]) -> ModelType:
        model_instance = self.model(**data)
        mongo_data = model_instance.to_mongo()
        result = await self.collection.insert_one(mongo_data)
        return await self.find_by_id(result.inserted_id)

    async def update(
            self,
            query: Dict,
            data: Dict[str, Any],
            upsert: bool = False
    ) -> Optional[ModelType]:
        update_data = {
            "$set": {
                **data,
                "updated_at": datetime.utcnow()
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
            id: Union[str, ObjectId],
            data: Dict[str, Any]
    ) -> Optional[ModelType]:
        if isinstance(id, str):
            id = ObjectId(id)
        return await self.update({"_id": id}, data)

    async def delete(self, query: Dict) -> bool:
        result = await self.collection.delete_one(query)
        return result.deleted_count > 0

    async def delete_by_id(self, id: Union[str, ObjectId]) -> bool:
        if isinstance(id, str):
            id = ObjectId(id)
        return await self.delete({"_id": id})