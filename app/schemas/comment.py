from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.core.date import convert_datetime_to_realworld


# 创建评论请求体
class CreateCommentData(BaseModel):
    body: str


class CreateCommentRequest(BaseModel):
    comment: CreateCommentData


# 评论作者结构（替代 ProfileDTO）
class Profile(BaseModel):
    username: str
    bio: str = ""
    image: Optional[str] = None
    following: bool = False
    id: Optional[int] = None


# 单个评论（响应用）
class Comment(BaseModel):
    id: int
    body: str
    author: Profile
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: convert_datetime_to_realworld}
    )


# 评论列表（响应用）
class CommentsListResponse(BaseModel):
    comments: List[Comment]
    comments_count: int = Field(alias="commentsCount")

    model_config = ConfigDict(populate_by_name=True)


# 单个评论响应
class CommentResponse(BaseModel):
    comment: Comment


# 可选：用于数据库操作或服务层处理（如果仍需要 author_id/article_id）
class InternalComment(BaseModel):
    id: int
    body: str
    author_id: int
    article_id: int
    created_at: datetime
    updated_at: datetime