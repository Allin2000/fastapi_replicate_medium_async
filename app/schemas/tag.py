import datetime
from pydantic import BaseModel

from sqlmodel.alembic_model import Tag


class TagDTO(BaseModel):
    id: int
    tag: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True

    @staticmethod
    def from_model(model: Tag) -> "TagDTO":
        return TagDTO(
            id=model.id,
            tag=model.tag,
            created_at=model.created_at
        )

    @staticmethod
    def to_model(dto: "TagDTO") -> Tag:
        model = Tag(tag=dto.tag)
        if hasattr(dto, "id"):
            model.id = dto.id
        return model



