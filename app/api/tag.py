from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tag import TagService
from app.schemas.tag import TagsResponse
from app.core.dep import get_db_session

router = APIRouter()


@router.get("", response_model=TagsResponse)
async def get_all_tags( session:AsyncSession=Depends(get_db_session),) -> TagsResponse:
    """
    Return available all tags.
    """
    tag_service = TagService()
    tags = await tag_service.list(session=session)
    return TagsResponse.from_tags(tag_objects=tags)
