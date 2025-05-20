from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tag import TagService
from app.schemas.tag import TagDTO
from app.core.dep import container

router = APIRouter()


@router.get("", response_model=list[TagDTO])
async def get_all_tags( session:AsyncSession=Depends(container.session),
                       tag_service:TagService=Depends(container.tag_service)
                       ) -> TagDTO:
    """
    Return available all tags.
    """
   
    tags = await tag_service.list(session=session)
    return tags
