from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tag import TagService
from app.schemas.tag import TagDTO
from app.core.dep import get_db_session,get_TagService

router = APIRouter()


@router.get("", response_model=list[TagDTO])
async def get_all_tags( session:AsyncSession=Depends(get_db_session),
                       tag_service:TagService=Depends(get_TagService)
                       ) -> TagDTO:
    """
    Return available all tags.
    """
   
    tags = await tag_service.list(session=session)
    return tags
