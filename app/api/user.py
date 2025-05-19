from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserUpdateDataDTO as UserUpdate, UserRegistrationResponse, CreatedUserDTO, UserDTO
from app.services.user import UserService
from app.core.dep import get_current_user, get_db_session, get_UserService
from app.schemas.user import UserWithID

router = APIRouter()


@router.get("", response_model=UserRegistrationResponse)
async def get_current_user(
    current_user: UserWithID = Depends(get_current_user),
    user_service: UserService = Depends(get_UserService),
    session: AsyncSession = Depends(get_db_session),
) -> UserRegistrationResponse:
    """
    Return current user with token (token can be generated or refreshed here).
    """
    # 获取完整 UserDTO 对象
    user_dto = await user_service.get(session=session, user_id=current_user.id)
    
    # 生成 token，这里假设 user_service 有 generate_token 方法，需自己实现
    token = user_service.generate_token(user_dto)
    
    # 使用 CurrentUserResponse.from_dto 创建响应数据
    return UserRegistrationResponse.from_dto(
        CreatedUserDTO(
            id=user_dto.id,
            email=user_dto.email,
            username=user_dto.username,
            bio=user_dto.bio,
            image=user_dto.image_url,
            token=token,
        )
    )


@router.put("", response_model=UserRegistrationResponse)
async def update_current_user(
    payload: UserUpdate,
    session: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(get_UserService),
    current_user: UserWithID = Depends(get_current_user),
) -> UserRegistrationResponse:
    """
    Update current user and return updated user with token.
    """
    # 调用 update 返回 UserUpdateDTO
    updated_user_dto = await user_service.update(session=session, user_id=current_user.id, update_item=payload)
    
    # 重新从数据库加载完整用户信息（包括密码哈希等），或者用 updated_user_dto 映射生成 token
    user_dto = await user_service.get(session=session, user_id=updated_user_dto.id)
    
    # 生成 token
    token = user_service.generate_token(user_dto)
    
    # 返回带token的响应
    return UserRegistrationResponse.from_dto(
        CreatedUserDTO(
            id=user_dto.id,
            email=user_dto.email,
            username=user_dto.username,
            bio=user_dto.bio,
            image=user_dto.image_url,
            token=token,
        )
    )