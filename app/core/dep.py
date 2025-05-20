from typing import Optional
import contextlib
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.schemas.user import UserDTO
from app.core.config import get_app_settings,BaseAppSettings
from app.schemas.auth import TokenPayload
from app.core.exception import IncorrectJWTTokenException


from app.services.article import ArticleService
from app.services.comment import CommentService
from app.services.auth_token import AuthTokenService
from app.services.user import UserService
from app.services.profile import ProfileService
from app.services.tag import TagService
from app.core.security import HTTPTokenHeader
from app.services.auth import UserAuthService
from app.services.favorite import FavoriteService
from app.services.follower import FollowerService

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncIterator


class Container:
    """Dependency injector project container."""

    def __init__(self, settings: BaseAppSettings) -> None:
        self._settings = settings
        self._engine = create_async_engine(**settings.sqlalchemy_engine_props)
        self._session = async_sessionmaker(bind=self._engine, expire_on_commit=False)



    @contextlib.asynccontextmanager
    async def context_session(self) -> AsyncIterator[AsyncSession]:
        session = self._session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()



    def auth_token_service(self) -> AuthTokenService:
        return AuthTokenService(
            secret_key=self._settings.jwt_secret_key,
            token_expiration_minutes=self._settings.jwt_token_expiration_minutes,
            algorithm=self._settings.jwt_algorithm,
        )
    

    def user_auth_service(self) -> UserAuthService:
        return UserAuthService(
            user_service=self.user_service(),
            auth_token_service=self.auth_token_service(),
        )
    
    def user_service(self) -> UserService:
        return UserService()
    
    def profile_service(self) -> ProfileService:
        return ProfileService(
            user_service=self.user_service()
            )
    

    def tag_service(self) -> TagService:
        return TagService()



    def article_service(self) -> ArticleService:
        return ArticleService()
    

    def comment_service(self) -> CommentService:
        return CommentService()
    
    def follower_service(self) -> FollowerService:
        return FollowerService()
    
    def favorite_service(self) -> FavoriteService:
        return FavoriteService()
    

        

container = Container(settings=get_app_settings())

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
    session: AsyncSession = Depends(container.session),
    token: str = Depends(token_security),
    auth_token_service: AuthTokenService = Depends(container.auth_token_service),
    user_service: UserService = Depends(container.user_auth_service),
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
    session: AsyncSession = Depends(container.session),
    token: str = Depends(token_security_optional),
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
