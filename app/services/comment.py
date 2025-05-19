from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.core.exception import CommentNotFoundException
from app.sqlmodel.alembic_model import Comment, User # 导入 User 模型
from app.schemas.comment import (
    CreateCommentDTO,
    CommentRecordDTO,  # 使用 CommentRecordDTO 替代 Comment
    CommentDTO,        # 用于更丰富的评论DTO
    CommentsListDTO    # 用于评论列表
)
from app.schemas.profile import ProfileDTO # 导入 ProfileDTO

class CommentService:

    async def add(
        self,
        session: AsyncSession,
        author_id: int,
        article_id: int,
        create_item: CreateCommentDTO,
    ) -> CommentRecordDTO: # 返回值改为 CommentRecordDTO
        query = (
            insert(Comment)
            .values(
                author_id=author_id,
                article_id=article_id,
                body=create_item.body,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            .returning(Comment)
        )
        result = await session.execute(query)
        # 将 SQLAlchemy 模型转换为 DTO
        comment_record = result.scalar_one()
        return CommentRecordDTO(
            id=comment_record.id,
            body=comment_record.body,
            author_id=comment_record.author_id,
            article_id=comment_record.article_id,
            created_at=comment_record.created_at,
            updated_at=comment_record.updated_at,
        )

    async def get_or_none(
        self, session: AsyncSession, comment_id: int
    ) -> Optional[CommentRecordDTO]: # 返回值改为 CommentRecordDTO
        query = select(Comment).where(Comment.id == comment_id)
        comment = await session.scalar(query)
        if comment:
            return CommentRecordDTO(
                id=comment.id,
                body=comment.body,
                author_id=comment.author_id,
                article_id=comment.article_id,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
        return None

    async def get(self, session: AsyncSession, comment_id: int) -> CommentRecordDTO: # 返回值改为 CommentRecordDTO
        query = select(Comment).where(Comment.id == comment_id)
        comment = await session.scalar(query)
        if not comment:
            raise CommentNotFoundException()
        return CommentRecordDTO(
            id=comment.id,
            body=comment.body,
            author_id=comment.author_id,
            article_id=comment.article_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    async def list(
        self, session: AsyncSession, article_id: int
    ) -> List[CommentRecordDTO]: # 返回值改为 List[CommentRecordDTO]
        query = select(Comment).where(Comment.article_id == article_id)
        comments = await session.scalars(query)
        return [
            CommentRecordDTO(
                id=c.id,
                body=c.body,
                author_id=c.author_id,
                article_id=c.article_id,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in comments
        ]

    async def delete(self, session: AsyncSession, comment_id: int) -> None:
        query = delete(Comment).where(Comment.id == comment_id)
        await session.execute(query)

    async def count(self, session: AsyncSession, article_id: int) -> int:
        query = select(count(Comment.id)).where(Comment.article_id == article_id)
        result = await session.execute(query)
        return result.scalar_one()

    async def get_comment_response(self, session: AsyncSession, comment: Comment) -> CommentDTO:
        """
        根据 Comment SQLAlchemy 模型构建 CommentDTO。
        """
        # 查询关联的作者信息
        author = await session.scalar(select(User).where(User.id == comment.author_id))
        if not author:
            # 根据你的业务逻辑处理找不到作者的情况，这里抛出异常
            raise Exception(f"Author with id {comment.author_id} not found")

        # 构建 ProfileDTO
        profile_dto = ProfileDTO(
            user_id=author.id,
            username=author.username,
            bio=author.bio,
            image=author.image_url,
            following=False,  # 此处 `following` 需要根据当前请求用户与作者的关系来判断
        )

        # 构建 CommentDTO
        return CommentDTO(
            id=comment.id,
            body=comment.body,
            author=profile_dto,
            createdAt=comment.created_at, # 注意这里是 createdAt 对应 DTO 中的 alias
            updatedAt=comment.updated_at, # 注意这里是 updatedAt 对应 DTO 中的 alias
        )

    async def list_comments_response(self, session: AsyncSession, comments: List[Comment]) -> CommentsListDTO:
        """
        根据 Comment SQLAlchemy 模型列表构建 CommentsListDTO。
        """
        comment_dtos = []
        for comment in comments:
            comment_dto = await self.get_comment_dto(session, comment)
            comment_dtos.append(comment_dto)
        return CommentsListDTO(comments=comment_dtos, commentsCount=len(comment_dtos))