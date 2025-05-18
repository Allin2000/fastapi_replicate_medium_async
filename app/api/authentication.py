from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas.user import (
    UserLoginData,
    UserRegistrationData,
    UserResponse,
)
from app.services.auth_token import AuthTokenService
from app.core.dep import get_db_session,get_AuthTokenService
from app.schemas.user import UserResponse as UserSchema

router = APIRouter()



@router.post("", response_model=UserResponse)
async def register_user(
    payload: UserRegistrationData,
 session:AsyncSession=Depends(get_db_session),
 user_auth_service:AuthTokenService=Depends(get_AuthTokenService)
) -> UserResponse:
    """
    Process user registration.
    """
    
    user = await user_auth_service.sign_up_user(session=session, user_to_create=payload)
    user_response = await user_auth_service.get_user_response_with_token(session=session, user=user)
    return UserResponse(user=user_response)


@router.post("/login", response_model=UserResponse)
async def login_user(
    payload: UserLoginData,  
      session:AsyncSession=Depends(get_db_session),
       user_auth_service:AuthTokenService=Depends(get_AuthTokenService)
) -> UserResponse:
    """
    Process user login.
    """
    user = await user_auth_service.sign_in_user(session=session, user_to_login=payload)
    user_response = await user_auth_service.get_user_response_with_token(session=session, user=user)
    return UserResponse(user=user_response)