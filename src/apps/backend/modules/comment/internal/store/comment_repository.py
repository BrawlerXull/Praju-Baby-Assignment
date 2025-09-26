from datetime import datetime

from pymongo import ReturnDocument
from pymongo.errors import OperationFailure

from modules.application.repository import ApplicationRepository
from modules.comment.internal.store.comment_model import CommentModel
from modules.logger.logger import Logger

COMMENT_VALIDATION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["task_id", "account_id", "content", "created_at", "updated_at", "active"],
        "properties": {
            "task_id": {"bsonType": "string"},
            "account_id": {"bsonType": "string"},
            "content": {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "active": {"bsonType": "bool"},
        },
    }
}


class CommentRepository(ApplicationRepository):
    collection_name = CommentModel.get_collection_name()

    @classmethod
    def on_init_collection(cls, collection) -> bool:
        # Index for faster queries on active comments per task
        collection.create_index(
            [("task_id", 1), ("active", 1)], name="task_id_active_index", partialFilterExpression={"active": True}
        )

        try:
            collection.database.command(
                {"collMod": cls.collection_name, "validator": COMMENT_VALIDATION_SCHEMA, "validationLevel": "strict"}
            )
        except OperationFailure as e:
            # If collection doesn't exist create it with validator
            if getattr(e, "code", None) == 26:
                collection.database.create_collection(cls.collection_name, validator=COMMENT_VALIDATION_SCHEMA)
            else:
                Logger.error(f"OperationFailure for collection comments: {getattr(e, 'details', str(e))}")
        return True

    @classmethod
    def insert_one(cls, comment_model: CommentModel) -> CommentModel:
        now = datetime.utcnow()
        doc = {
            "task_id": comment_model.task_id,
            "account_id": comment_model.account_id,
            "content": comment_model.content,
            "created_at": now,
            "updated_at": now,
            "active": True,
        }

        result = cls.collection().insert_one(doc)
        comment_model.id = result.inserted_id
        comment_model.created_at = now
        comment_model.updated_at = now
        comment_model.active = True
        return comment_model

    @classmethod
    def find_one(cls, filter_query: dict) -> dict | None:
        return cls.collection().find_one(filter_query)

    @classmethod
    def find_paginated(cls, filter_query: dict, pagination_params) -> tuple[list[dict], int]:
        """
        Returns (items_list_of_docs, total_count).
        `pagination_params` expected to be an instance of PaginationParams or a dict with page/size.
        """
        # Accept both dataclass PaginationParams or dict
        page = getattr(pagination_params, "page", None) or pagination_params.get("page", 1)
        size = getattr(pagination_params, "size", None) or pagination_params.get("size", 10)
        if page < 1:
            page = 1
        if size < 1:
            size = 10
        skip = (page - 1) * size

        cursor = cls.collection().find(filter_query).sort("created_at", -1).skip(skip).limit(size)
        items = list(cursor)
        total = cls.collection().count_documents(filter_query)
        return items, total

    @classmethod
    def find_by_task_id(cls, task_id: str) -> list[CommentModel]:
        docs = cls.collection().find({"task_id": task_id, "active": True}).sort("created_at", -1)
        return [CommentModel.from_bson(d) for d in docs]

    @classmethod
    def update_one(cls, filter_query: dict, update_data: dict) -> dict | None:
        return cls.collection().find_one_and_update(filter_query, update_data, return_document=ReturnDocument.AFTER)
