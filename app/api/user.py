from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserUpdateDataDTO , UserRegistrationResponse, UserDTO
from app.services.user import UserService
from app.core.dep import get_current_user,container,token_security
from app.core.security import HTTPException

router = APIRouter()




@router.get("", response_model=UserRegistrationResponse)
async def get_current_user(
    token: HTTPException=Depends(token_security),
    current_user: UserDTO = Depends(get_current_user),
) -> UserRegistrationResponse:
    """
    获取当前用户详细信息，并返回带 token 的响应。
    """
    return UserRegistrationResponse.from_dto(current_user, token=token)




@router.put("", response_model=UserRegistrationResponse)
async def update_current_user(
    payload: UserUpdateDataDTO,
    token: HTTPException=Depends(token_security),
    current_user: UserDTO = Depends(get_current_user),
    user_service: UserService = Depends(token_security),
    session: AsyncSession = Depends(container.session),
) -> UserRegistrationResponse:
    """
    更新当前用户信息，并返回更新后的用户和 token。
    """
    # 更新用户
    updated_user_dto = await user_service.update(
        session=session,
        user_id=current_user.id,
        update_item=payload
    )


   

    return UserRegistrationResponse.from_dto(updated_user_dto, token=token)