from typing import Annotated, Optional,Generator

from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.schemas.user import UserDTO
from app.services.user import UserService
from app.core.config import get_app_settings
from app.schemas.auth import TokenPayload #Import TokenPayload
from app.services.auth_token import AuthTokenService
from app.core.exception import IncorrectJWTTokenException

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel.sql_service import SessionLocal
from app.services.article import ArticleService
from app.services.comment import CommentService
from app.services.article_tag import ArticleTagService
from app.services.auth_token import AuthTokenService
from app.services.favorite import FavoriteService
from app.services.follower import FollowerService
from app.services.article_tag import ArticleTagService
from app.services.user import UserService
from app.services.profile import ProfileService
from app.services.tag import TagService
from app.sqlmodel.sql_service import DatabaseService
from app.core.security import HTTPTokenHeader
from app.services.auth import UserAuthService

def get_Article_service():
    return ArticleService()

def get_CommentService():
    return CommentService()

def get_ArticleTagService():
    return ArticleTagService()

def get_AuthTokenService():
    return AuthTokenService()

def get_FavoriteService():
    return FavoriteService()

def get_FollowerService():
    return FollowerService()

def get_ArticleTagService():
    return ArticleTagService()

def get_UserService():
    return UserService()

def get_ProfileService():
    return ProfileService()

def get_TagService():
    return TagService()

def get_DatabaseService():
    return DatabaseService()

def get_HTTPTokenHeader():
    return HTTPTokenHeader()

def get_UserAuthService():
    return UserAuthService()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


token_security = HTTPTokenHeader(
    name="Authorization",
    scheme_name="JWT Token",
    description="Token Format: `Token xxxxxx.yyyyyyy.zzzzzz`",
    raise_error=True,
)
token_security_optional = HTTPTokenHeader(
    name="Authorization",
    scheme_name="JWT Token",
    description="Token Format: `Token xxxxxx.yyyyyyy.zzzzzz`",
    raise_error=False,
)



async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
    token: str = Depends(HTTPTokenHeader(raise_error=True, name="Authorization")),
    auth_token_service: AuthTokenService = Depends(AuthTokenService),
    user_service: UserService = Depends(UserService),
) -> UserDTO:
    """
    获取当前用户，必须提供有效的 token，否则返回 401 错误。
    """
    try:
        token_payload: TokenPayload = auth_token_service.parse_jwt_token(token)
    except IncorrectJWTTokenException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await user_service.get_user_by_id(session=session, user_id=token_payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserDTO(
        id=user.id,
        email=user.email,
        username=user.username,
        bio=user.bio,
        image=user.image_url,
        token=token,
    )

async def get_current_user_or_none(
    session: AsyncSession = Depends(get_db_session),
    token: str = Depends(HTTPTokenHeader(raise_error=False, name="Authorization")),
    auth_token_service: AuthTokenService = Depends(AuthTokenService),
    user_service: UserService = Depends(UserService),
) -> Optional[UserDTO]:
    """
    尝试获取当前用户，如果无效或未提供 token，返回 None。
    """
    if not token:
        return None

    try:
        token_payload: TokenPayload = auth_token_service.parse_jwt_token(token)
    except IncorrectJWTTokenException:
        return None

    user = await user_service.get_user_by_id(session=session, user_id=token_payload.user_id)
    if not user:
        return None

    return UserDTO(
        id=user.id,
        email=user.email,
        username=user.username,
        bio=user.bio,
        image=user.image_url,
        token=token,
    )
