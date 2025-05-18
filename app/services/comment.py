from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.core.exception import CommentNotFoundException
from app.sqlmodel.alembic_model import Comment
from app.schemas.comment import CreateCommentData as CreateCommentDTO, Comment as CommentSchema  # 导入 Pydantic 模型


class CommentService:
    """Service for Comment model, without DTO conversion."""

    async def add(
        self,
        session: AsyncSession,
        author_id: int,
        article_id: int,
        create_item: CreateCommentDTO,
    ) -> Comment:
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
        return result.scalar_one()

    async def get_or_none(
        self, session: AsyncSession, comment_id: int
    ) -> Optional[Comment]:
        query = select(Comment).where(Comment.id == comment_id)
        return await session.scalar(query)

    async def get(self, session: AsyncSession, comment_id: int) -> Comment:
        query = select(Comment).where(Comment.id == comment_id)
        comment = await session.scalar(query)
        if not comment:
            raise CommentNotFoundException()
        return comment

    async def list(
        self, session: AsyncSession, article_id: int
    ) -> List[Comment]:
        query = select(Comment).where(Comment.article_id == article_id)
        comments = await session.scalars(query)
        return list(comments)

    async def delete(self, session: AsyncSession, comment_id: int) -> None:
        query = delete(Comment).where(Comment.id == comment_id)
        await session.execute(query)

    async def count(self, session: AsyncSession, article_id: int) -> int:
        query = select(count(Comment.id)).where(Comment.article_id == article_id)
        result = await session.execute(query)
        return result.scalar_one()

    async def get_comment_response(self, session: AsyncSession, comment: Comment) -> CommentSchema:
        # 这里你需要查询关联的用户信息来构建 CommentSchema
        from app.sqlmodel.alembic_model import User  # 避免循环导入

        author = await session.scalar(select(User).where(User.id == comment.author_id))
        if not author:
            # 处理找不到作者的情况，可以抛出异常或返回默认值
            raise Exception(f"Author with id {comment.author_id} not found")

        return CommentSchema(
            id=comment.id,
            createdAt=comment.created_at,
            updatedAt=comment.updated_at,
            body=comment.body,
            author=CommentSchema.Author(
                username=author.username,
                bio=author.bio,
                image=author.image_url,
                following=False,  # 需要根据当前用户判断是否关注
            ),
        )

    async def list_comment_responses(self, session: AsyncSession, comments: List[Comment]) -> List[CommentSchema]:
        comment_responses = []
        for comment in comments:
            comment_response = await self.get_comment_response(session, comment)
            comment_responses.append(comment_response)
        return comment_responses