from typing import Optional

from flask import jsonify, request
from flask.typing import ResponseReturnValue
from flask.views import MethodView

from modules.application.common.types import PaginationParams
from modules.authentication.rest_api.access_auth_middleware import access_auth_middleware
from modules.comment.comment_service import CommentService
from modules.comment.errors import CommentBadRequestError
from modules.comment.types import (
    CreateCommentParams,
    DeleteCommentParams,
    GetCommentParams,
    GetPaginatedCommentsParams,
    UpdateCommentParams,
)


class CommentView(MethodView):
    @access_auth_middleware
    def post(self, task_id: str) -> ResponseReturnValue:
        data = request.get_json()
        if not data or not data.get("content"):
            raise CommentBadRequestError("Content is required")

        account_id = getattr(request, "account_id")
        params = CreateCommentParams(task_id=task_id, account_id=account_id, content=data["content"])
        comment = CommentService.create_comment(params=params)
        return jsonify(comment), 201

    @access_auth_middleware
    def get(self, task_id: str, comment_id: Optional[str] = None) -> ResponseReturnValue:
        if comment_id:
            params = GetCommentParams(comment_id=comment_id, task_id=task_id)
            comment = CommentService.get_comment(params=params)
            return jsonify(comment), 200
        else:
            page = request.args.get("page", type=int)
            size = request.args.get("size", type=int)

            if page is not None and page < 1:
                raise CommentBadRequestError("Page must be greater than 0")
            if size is not None and size < 1:
                raise CommentBadRequestError("Size must be greater than 0")

            if page is None:
                page = PaginationParams(page=1, size=10, offset=0).page
            if size is None:
                size = PaginationParams(page=1, size=10, offset=0).size

            pagination_params = PaginationParams(page=page, size=size, offset=0)
            params = GetPaginatedCommentsParams(task_id=task_id, pagination_params=pagination_params)
            pagination_result = CommentService.get_paginated_comments(params=params)

            # convert PaginationResult dataclass to dict
            response_data = {
                "items": pagination_result.items,
                "pagination_params": {
                    "page": pagination_result.pagination_params.page,
                    "size": pagination_result.pagination_params.size,
                    "offset": pagination_result.pagination_params.offset,
                },
                "total_count": pagination_result.total_count,
                "total_pages": pagination_result.total_pages,
            }

            return jsonify(response_data), 200

    @access_auth_middleware
    def patch(self, task_id: str, comment_id: str) -> ResponseReturnValue:
        data = request.get_json()
        if not data or not data.get("content"):
            raise CommentBadRequestError("Content is required")
        params = UpdateCommentParams(comment_id=comment_id, task_id=task_id, content=data["content"])
        updated_comment = CommentService.update_comment(params=params)
        return jsonify(updated_comment), 200

    @access_auth_middleware
    def delete(self, task_id: str, comment_id: str) -> ResponseReturnValue:
        params = DeleteCommentParams(comment_id=comment_id, task_id=task_id)
        CommentService.delete_comment(params=params)
        return "", 204
