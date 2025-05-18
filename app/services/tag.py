from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sqlmodel.alembic_model import Tag
from app.schemas.tag import Tag as TagDTO  # 导入 Pydantic 模型


class TagService:
    """Service for Tag model, without DTO conversion."""

    async def list(self, session: AsyncSession) -> list[Tag]:
        query = select(Tag).order_by(Tag.created_at.desc())
        tags = await session.scalars(query)
        return [self.get_tag_response(tag) for tag in tags]

    async def get_tag_response(self, tag: Tag) -> TagDTO:
        return TagDTO(
            id=tag.id,
            tag=tag.tag,
            createdAt=tag.created_at,
        )

