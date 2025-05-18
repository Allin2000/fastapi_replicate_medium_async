from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.sqlmodel.alembic_model import ArticleTag, Tag  # 导入 SQLAlchemy 的 Tag 模型


class ArticleTagService:
    """Repository for Article Tag model, without DTO conversion."""

    async def add_many(
        self, session: AsyncSession, article_id: int, tags: list[str]
    ) -> list[Tag]:  # 直接返回 SQLAlchemy 的 Tag 模型列表
        insert_tag_query = (
            insert(Tag)
            .on_conflict_do_nothing()
            .values([{"tag": tag, "created_at": datetime.now()} for tag in tags])
            .returning(Tag)  # 返回插入或已存在的 Tag 对象
        )
        result = await session.execute(insert_tag_query)
        tag_objects = result.scalars().all()

        link_values = [
            {"article_id": article_id, "tag_id": tag.id, "created_at": datetime.now()}
            for tag in tag_objects
        ]
        insert_link_query = insert(ArticleTag).on_conflict_do_nothing().values(link_values)
        await session.execute(insert_link_query)
        await session.commit()  # 确保数据写入

        return list(tag_objects)

    async def list(self, session: AsyncSession, article_id: int) -> list[Tag]:
        query = (
            select(Tag)
            .join(ArticleTag, (ArticleTag.tag_id == Tag.id) & (ArticleTag.article_id == article_id))
            .order_by(Tag.created_at.desc())
        )
        result = await session.execute(query)
        tags = result.scalars().all()
        return list(tags)