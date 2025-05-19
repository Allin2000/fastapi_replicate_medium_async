from typing import Annotated, Optional,Generator

from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.schemas.user import UserWithID
from app.services.user import UserService
from app.core.config import get_app_settings
from app.schemas.auth import TokenPayload #Import TokenPayload
from app.services.auth_token import AuthTokenService
from app.core.exception import IncorrectJWTTokenException

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel.sql_service import SessionLocal
from collections.abc import AsyncIterator
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




async def get_current_user(
   session:AsyncSession=Depends(get_db_session),
    authorization: Optional[str] = Header(None),
) -> UserWithID:
    """
    获取当前登录用户。如果无效或缺失的 token，将抛出 401 错误。
    """
    settings = get_app_settings()
    auth_token_service = AuthTokenService(
        secret_key=settings.secret_key,
        token_expiration_minutes=settings.token_expiration_minutes,
        algorithm=settings.algorithm,
    )
    user_service = UserService()

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    try:
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Must be 'Bearer'",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Must be 'Bearer <token>'",
        )

    try:
        token_payload: TokenPayload = auth_token_service.parse_jwt_token(token=token)
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

    return UserWithID(
        id=user.id,
        email=user.email,
        username=user.username,
        bio=user.bio,
        image=user.image_url,
        token=token,
    )

async def get_current_user_or_none(
   session:AsyncSession=Depends(get_db_session),
    authorization: Optional[str] = Header(None),
) -> Optional[UserWithID]:
    """
    获取当前登录用户。如果 token 无效或未提供，返回 None。
    """
    settings = get_app_settings()
    auth_token_service = AuthTokenService(
        secret_key=settings.secret_key,
        token_expiration_minutes=settings.token_expiration_minutes,
        algorithm=settings.algorithm,
    )
    user_service = UserService()

    if not authorization:
        return None

    try:
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        token_payload: TokenPayload = auth_token_service.parse_jwt_token(token=token)
    except IncorrectJWTTokenException:
        return None

    user = await user_service.get_user_by_id(session=session, user_id=token_payload.user_id)
    if not user:
        return None

    return UserWithID(
        id=user.id,
        email=user.email,
        username=user.username,
        bio=user.bio,
        image=user.image_url,
        token=token,
    )

