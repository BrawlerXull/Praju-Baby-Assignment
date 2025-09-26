# backend/modules/comment/rest_api/comment_rest_api_server.py
from flask import Blueprint

from modules.comment.rest_api.comment_router import CommentRouter


class CommentRestApiServer:
    @staticmethod
    def create() -> Blueprint:
        blueprint = Blueprint("comment_api", __name__)
        return CommentRouter.create_route(blueprint=blueprint)
