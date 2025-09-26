from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union

from bson import ObjectId

from modules.application.base_model import BaseModel


@dataclass
class CommentModel(BaseModel):
    task_id: str
    account_id: str
    content: str
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    id: Optional[Union[ObjectId, str]] = None
    active: bool = True

    @classmethod
    def from_bson(cls, bson_data: dict) -> "CommentModel":
        return cls(
            task_id=bson_data.get("task_id", ""),
            account_id=bson_data.get("account_id", ""),
            content=bson_data.get("content", ""),
            id=bson_data.get("_id"),
            created_at=bson_data.get("created_at"),
            updated_at=bson_data.get("updated_at"),
            active=bson_data.get("active", True),
        )

    def to_bson(self) -> dict:
        """
        Convert model to JSON-serializable dict.
        ObjectId -> str, datetime -> ISO string
        """
        return {
            "id": str(self.id) if self.id else None,
            "task_id": self.task_id,
            "account_id": self.account_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "active": self.active,
        }

    @staticmethod
    def get_collection_name() -> str:
        return "comments"
