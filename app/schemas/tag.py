import datetime
from pydantic import BaseModel


class Tag(BaseModel):
    id: int
    tag: str
    created_at: datetime.datetime


class TagsResponse(BaseModel):
    tags: list[str]

    @classmethod
    def from_tags(cls, tag_objects: list[Tag]) -> "TagsResponse":
        return TagsResponse(tags=[t.tag for t in tag_objects])