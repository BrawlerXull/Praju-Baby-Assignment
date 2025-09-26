from datetime import datetime

from bson import ObjectId

from modules.application.common.types import PaginationResult
from modules.comment.errors import CommentNotFoundError
from modules.comment.internal.store.comment_model import CommentModel
from modules.comment.internal.store.comment_repository import CommentRepository
from modules.comment.types import (
    CreateCommentParams,
    DeleteCommentParams,
    GetCommentParams,
    GetPaginatedCommentsParams,
    UpdateCommentParams,
)


class CommentService:
    @staticmethod
    def create_comment(*, params: CreateCommentParams) -> dict:
        model = CommentModel(task_id=params.task_id, account_id=params.account_id, content=params.content)
        inserted = CommentRepository.insert_one(model)
        # convert to dict consistent with other modules
        return inserted.to_bson()

    @staticmethod
    def get_comment(*, params: GetCommentParams) -> dict:
        try:
            oid = ObjectId(params.comment_id)
        except Exception:
            raise CommentNotFoundError(params.comment_id)

        doc = CommentRepository.find_one({"_id": oid, "task_id": params.task_id, "active": True})
        if not doc:
            raise CommentNotFoundError(params.comment_id)
        return CommentModel.from_bson(doc).to_bson()

    @staticmethod
    def get_paginated_comments(*, params: GetPaginatedCommentsParams) -> PaginationResult[dict]:
        # expects params.pagination_params to be a PaginationParams instance
        filter_query = {"task_id": params.task_id, "active": True}
        items_docs, total = CommentRepository.find_paginated(filter_query, params.pagination_params)

        # convert docs -> dicts
        items = [CommentModel.from_bson(d).to_bson() for d in items_docs]

        # compute total_pages
        params.pagination_params.page
        size = params.pagination_params.size
        total_pages = (total + size - 1) // size if total > 0 else 0

        return PaginationResult(
            items=items, pagination_params=params.pagination_params, total_count=total, total_pages=total_pages
        )

    @staticmethod
    def update_comment(*, params: UpdateCommentParams) -> dict:
        try:
            oid = ObjectId(params.comment_id)
        except Exception:
            raise CommentNotFoundError(params.comment_id)

        existing = CommentRepository.find_one({"_id": oid, "task_id": params.task_id, "active": True})
        if not existing:
            raise CommentNotFoundError(params.comment_id)

        updated_doc = CommentRepository.update_one(
            {"_id": oid}, {"$set": {"content": params.content, "updated_at": datetime.utcnow()}}
        )
        if not updated_doc:
            raise CommentNotFoundError(params.comment_id)
        return CommentModel.from_bson(updated_doc).to_bson()

    @staticmethod
    def delete_comment(*, params: DeleteCommentParams) -> bool:
        try:
            oid = ObjectId(params.comment_id)
        except Exception:
            raise CommentNotFoundError(params.comment_id)

        existing = CommentRepository.find_one({"_id": oid, "task_id": params.task_id, "active": True})
        if not existing:
            raise CommentNotFoundError(params.comment_id)

        CommentRepository.collection().update_one(
            {"_id": oid}, {"$set": {"active": False, "updated_at": datetime.utcnow()}}
        )
        return True
