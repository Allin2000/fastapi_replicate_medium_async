from typing import Annotated, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.schemas.profile import ProfileResponse
from app.schemas.user import UserResponse as UserSchema
from app.services.profile import ProfileService
from app.services.follower import FollowerService
from app.core.dep import get_current_user, get_current_user_or_none,get_db_session,get_ProfileService,get_FollowerService

router = APIRouter()



@router.get("/{username}", response_model=ProfileResponse)
async def get_user_profile(
    username: str,
 session:AsyncSession=Depends(get_db_session),
 current_user:Optional[UserSchema]=Depends(get_current_user_or_none),
 profile_service:ProfileService=Depends(get_ProfileService)
) -> ProfileResponse:
    """
    Return user profile information.
    """
   
    profile = await profile_service.get_profile(session=session, username=username)
    following = False
    if current_user:
        from app.services.follower import FollowerService
        follower_service = FollowerService()
        following = await follower_service.exists(session, current_user.id, profile.id)
    profile_response = ProfileResponse(
        profile=ProfileResponse.Profile(
            username=profile.username,
            bio=profile.bio,
            image=profile.image_url,
            following=following,
        )
    )
    return profile_response


@router.post("/{username}/follow", response_model=ProfileResponse)
async def follow_username(
    username: str,
 session:AsyncSession=Depends(get_db_session),
  current_user:UserSchema=Depends(get_current_user),
   profile_service:ProfileService=Depends(get_ProfileService)
) -> ProfileResponse:
    """
    Follow profile with specific username.
    """
    user_to_follow = await profile_service._get_user_by_username(session=session, username=username)
    if current_user.id == user_to_follow.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")
    from app.services.follower import FollowerService
    follower_service = FollowerService()
    await follower_service.create(session, current_user.id, user_to_follow.id)
    profile = await profile_service.get_profile(session=session, username=username)
    profile_response = ProfileResponse(
        profile=ProfileResponse.Profile(
            username=profile.username,
            bio=profile.bio,
            image=profile.image_url,
            following=True,
        )
    )
    return profile_response


@router.delete("/{username}/follow", response_model=ProfileResponse)
async def unfollow_username(
    username: str,
 session:AsyncSession=Depends(get_db_session),
  current_user:UserSchema=Depends(get_current_user),
   profile_service:ProfileService=Depends(get_ProfileService),
follower_service:FollowerService=Depends(get_FollowerService)
) -> ProfileResponse:
    """
    Unfollow profile with specific username
    """
    user_to_unfollow = await profile_service._get_user_by_username(session=session, username=username)
    if current_user.id == user_to_unfollow.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot unfollow yourself")
   
    await follower_service.delete(session, current_user.id, user_to_unfollow.id)
    profile = await profile_service.get_profile(session=session, username=username)
    profile_response = ProfileResponse(
        profile=ProfileResponse.Profile(
            username=profile.username,
            bio=profile.bio,
            image=profile.image_url,
            following=False,
        )
    )
    return profile_response