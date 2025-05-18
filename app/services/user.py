from collections.abc import Collection
from datetime import datetime
from typing import Optional, List

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import UserNotFoundException
from app.schemas.user import UserRegistrationData, UserUpdateData, UserBase
from app.sqlmodel.alembic_model import User
from app.services.password import get_password_hash


class UserService:
    """Service for User model, without DTO conversion."""

    async def add(self, session: AsyncSession, create_item: UserRegistrationData) -> User:
        query = (
            insert(User)
            .values(
                username=create_item.username,
                email=create_item.email,
                password_hash=get_password_hash(create_item.password),
                image_url="https://api.realworld.io/images/smiley-cyrus.jpeg",
                bio="",
                created_at=datetime.now(),
            )
            .returning(User)
        )
        result = await session.execute(query)
        await session.commit()
        return result.scalar_one()

    async def get_by_email_or_none(
        self, session: AsyncSession, email: str
    ) -> Optional[User]:
        query = select(User).where(User.email == email)
        return await session.scalar(query)

    async def get_by_email(self, session: AsyncSession, email: str) -> User:
        query = select(User).where(User.email == email)
        user = await session.scalar(query)
        if not user:
            raise UserNotFoundException()
        return user

    async def get_or_none(self, session: AsyncSession, user_id: int) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        return await session.scalar(query)

    async def get(self, session: AsyncSession, user_id: int) -> User:
        query = select(User).where(User.id == user_id)
        user = await session.scalar(query)
        if not user:
            raise UserNotFoundException()
        return user

    async def list_by_users(
        self, session: AsyncSession, user_ids: Collection[int]
    ) -> List[User]:
        query = select(User).where(User.id.in_(user_ids))
        users = await session.scalars(query)
        return list(users)

    async def get_by_username_or_none(
        self, session: AsyncSession, username: str
    ) -> Optional[User]:
        query = select(User).where(User.username == username)
        return await session.scalar(query)

    async def get_by_username(self, session: AsyncSession, username: str) -> User:
        query = select(User).where(User.username == username)
        user = await session.scalar(query)
        if not user:
            raise UserNotFoundException()
        return user

    async def update(
        self, session: AsyncSession, user_id: int, update_item: UserUpdateData 
    ) -> User:
        query = (
            update(User)
            .where(User.id == user_id)
            .values(updated_at=datetime.now())
            .returning(User)
        )
        if update_item.username is not None:
            query = query.values(username=update_item.username)
        if update_item.email is not None:
            query = query.values(email=update_item.email)
        if update_item.password is not None:
            query = query.values(password_hash=get_password_hash(update_item.password))
        if update_item.bio is not None:
            query = query.values(bio=update_item.bio)
        if update_item.image_url is not None:
            query = query.values(image_url=update_item.image_url)

        result = await session.execute(query)
        await session.commit()
        return result.scalar_one()

    async def get_user_response(self, user: User, following: bool = False) -> UserBase:
        return UserBase(
            id=user.id,
            email=user.email,
            username=user.username,
            bio=user.bio,
            image=user.image_url,
            following=following,
            createdAt=user.created_at,
            updatedAt=user.updated_at,
        )
