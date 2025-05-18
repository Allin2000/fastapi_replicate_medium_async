from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends


from app.schemas.user import UserUpdateData as UserUpdate, UserResponse
from app.services.user import UserService
from app.core.dep import get_current_user,get_db_session,get_UserService
from app.schemas.user import UserWithID

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()



@router.get("", response_model=UserResponse)
async def get_current_user(
 current_user:UserWithID=Depends(get_current_user),
   user_service:UserService=Depends(get_UserService)
) -> UserResponse:
    """
    Return current user.
    """
  
    user_response = await user_service.get_user_response_with_token(session=None, user=current_user) # Session might not be needed here
    return UserResponse(user=user_response)


@router.put("", response_model=UserResponse)
async def update_current_user(
    payload: UserUpdate,
 session:AsyncSession=Depends(get_db_session),
    user_service:UserService=Depends(get_UserService),
 current_user:UserWithID=Depends(get_current_user),
) -> UserResponse:
    """
    Update current user.
    """

    updated_user = await user_service.update(session=session, user_id=current_user.id, update_item=payload)
    updated_user_response = await user_service.get_user_response_with_token(session=session, user=updated_user)
    return UserResponse(user=updated_user_response)