from fastapi import APIRouter, Path, Depends
from starlette import status
from typing import Optional

from app.schemas.comment import CreateCommentRequest
from app.schemas.comment import CommentResponse, CommentsListResponse
from app.schemas.user import UserResponse as UserSchema
from app.core.dep import (
    get_current_user_or_none,
    get_current_user,
    get_db_session,
    get_CommentService
)
from app.services.comment import CommentService
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.get("/{slug}/comments", response_model=CommentsListResponse)
async def get_comments(
    slug: str,
 session:AsyncSession=Depends(get_db_session),
    current_user:Optional[UserSchema]=Depends(get_current_user_or_none),
  comment_service:CommentService=Depends(get_CommentService)
) -> CommentsListResponse:
    """
    Get comments for an article.
    """
  
    comment_list_dto = await comment_service.get_article_comments(
        session=session, slug=slug, current_user=current_user
    )
    return CommentsListResponse.from_dto(dto=comment_list_dto)


@router.post("/{slug}/comments", response_model=CommentResponse)
async def create_comment(
    slug: str,
    payload: CreateCommentRequest,
  session:AsyncSession=Depends(get_db_session),
 current_user:UserSchema=Depends(get_current_user),
  comment_service:CommentService=Depends(get_CommentService)
) -> CommentResponse:
    """ 
    Create a comment for an article.
    """
    comment_dto = await comment_service.create_article_comment(
        session=session,
        slug=slug,
        comment_to_create=payload.to_dto(),
        current_user=current_user,
    )
    return CommentResponse.from_dto(dto=comment_dto)


@router.delete("/{slug}/comments/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    slug: str,
 session:AsyncSession=Depends(get_db_session),
 current_user:UserSchema=Depends(get_current_user),
  comment_service:CommentService=Depends(get_CommentService),
    comment_id: int = Path(..., alias="id"),
) -> None:
    """
    Delete a comment for an article.
    """

    await comment_service.delete_article_comment(
        session=session, slug=slug, comment_id=comment_id, current_user=current_user
    )
