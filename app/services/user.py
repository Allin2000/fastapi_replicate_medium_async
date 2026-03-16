
from collections.abc import Collection
from datetime import datetime
from typing import Optional, List

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import (
    UserNotFoundException,
    EmailAlreadyTakenException,
    UserNameAlreadyTakenException,
)
from app.schemas.user import (
    UserRegistrationDataDTO,
    UserUpdateDataDTO,
    UserUpdateDTO,
    UserDTO
)
from app.sqlmodel.alembic_model import User
from app.services.password import get_password_hash



class UserService:
    """Service for User model, using only DTO models."""

    @staticmethod
    def _to_dto(user: User) -> UserDTO:
        return UserDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            bio=user.bio,
            image_url=user.image_url,
            created_at=user.created_at,
        )

    async def add(self, session: AsyncSession, create_item: UserRegistrationDataDTO) -> UserDTO:
        existing_user_by_email = await self.get_by_email_or_none(session, create_item.email)
        if existing_user_by_email:
            raise EmailAlreadyTakenException()

        existing_user_by_username = await self.get_by_username_or_none(session, create_item.username)
        if existing_user_by_username:
            raise UserNameAlreadyTakenException()

        query = (
            insert(User)
            .values(
                username=create_item.username,
                email=create_item.email,
                password_hash=get_password_hash(create_item.password),
                image_url=None,
                bio=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            .returning(User)
        )
        result = await session.execute(query)
        await session.commit()
        user = result.scalar_one()
        return self._to_dto(user)

    async def get_by_email_or_none(self, session: AsyncSession, email: str) -> Optional[UserDTO]:
        query = select(User).where(User.email == email)
        user = await session.scalar(query)
        if not user:
            return None
        return self._to_dto(user)

    async def get_by_email(self, session: AsyncSession, email: str) -> UserDTO:
        query = select(User).where(User.email == email)
        user = await session.scalar(query)
        if not user:
            raise UserNotFoundException()
        return self._to_dto(user)

    async def get_user_by_id_or_none(self, session: AsyncSession, user_id: int) -> Optional[UserDTO]:
        query = select(User).where(User.id == user_id)
        user = await session.scalar(query)
        if not user:
            return None
        return self._to_dto(user)

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> UserDTO:
        query = select(User).where(User.id == user_id)
        user = await session.scalar(query)
        if not user:
            raise UserNotFoundException()
        return self._to_dto(user)

    async def list_by_users(self, session: AsyncSession, user_ids: Collection[int]) -> List[UserDTO]:
        query = select(User).where(User.id.in_(user_ids))
        users = await session.scalars(query)
        return [self._to_dto(user) for user in users]

    async def get_by_username_or_none(self, session: AsyncSession, username: str) -> Optional[UserDTO]:
        query = select(User).where(User.username == username)
        user = await session.scalar(query)
        if not user:
            return None
        return self._to_dto(user)

    async def get_by_username(self, session: AsyncSession, username: str) -> UserDTO:
        query = select(User).where(User.username == username)
        user = await session.scalar(query)
        if not user:
            raise UserNotFoundException()
        return self._to_dto(user)

    async def update(self, session: AsyncSession, user_id: int, update_item: UserUpdateDataDTO) -> UserUpdateDTO:
        current_user = await self.get_user_by_id(session, user_id)

        if update_item.username and update_item.username != current_user.username:
            user_with_username = await self.get_by_username_or_none(session, update_item.username)
            if user_with_username:
                raise UserNameAlreadyTakenException()

        if update_item.email and update_item.email != current_user.email:
            user_with_email = await self.get_by_email_or_none(session, update_item.email)
            if user_with_email:
                raise EmailAlreadyTakenException()

        update_data = update_item.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        if "image" in update_data:
            update_data["image_url"] = update_data.pop("image")

        query = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data, updated_at=datetime.now())
            .returning(User)
        )

        result = await session.execute(query)
        await session.commit()
        updated_user = result.scalar_one()

        # 返回 UpdatedUserDTO
        return UserUpdateDTO(
            id=updated_user.id,
            email=updated_user.email,
            username=updated_user.username,
            bio=updated_user.bio,
            image_url=updated_user.image_url,
        )