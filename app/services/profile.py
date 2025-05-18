from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exception import (
    OwnProfileFollowingException,
    ProfileAlreadyFollowedException,
    ProfileNotFollowedFollowedException,
    ProfileNotFoundException,
    UserNotFoundException,
)
from app.schemas.profile import Profile as ProfileSchema  # Import Pydantic Profile
from app.schemas.user import UserBase as UserSchema
from app.sqlmodel.sql_service import DatabaseService
from app.services.user import UserService


logger = get_logger()


class ProfileService:
    """Service to handle user profiles and following logic, using Pydantic."""

    def __init__(self, user_service: UserService, database_service: DatabaseService):
        self._user_service = user_service
        self._database_service = database_service

    async def get_profile_by_username(
        self, session: AsyncSession, username: str, current_user: Optional[UserSchema] = None
    ) -> ProfileSchema:
        try:
            target_user = await self._user_service.get_user_by_username(
                session=session, username=username
            )
        except UserNotFoundException:
            logger.exception("Profile not found", username=username)
            raise ProfileNotFoundException()

        profile = ProfileSchema(
            user_id=target_user.id,
            username=target_user.username,
            bio=target_user.bio,
            image=target_user.image_url,
            following=False,  # Default value
        )
        if current_user:
            # Directly use the session from database_service
            async with self._database_service.get_db() as session:
                profile.following = await self._check_following(
                    session=session, follower_id=current_user.id, following_id=target_user.id
                )
        return profile

    async def get_profile_by_user_id(
        self, session: AsyncSession, user_id: int, current_user: Optional[UserSchema] = None
    ) -> ProfileSchema:
        target_user = await self._user_service.get_user_by_id(session=session, user_id=user_id)

        profile = ProfileSchema(
            user_id=target_user.id,
            username=target_user.username,
            bio=target_user.bio,
            image=target_user.image_url,
            following=False,  # Default
        )

        if current_user:
            async with self._database_service.get_db() as session:
                profile.following = await self._check_following(
                    session=session, follower_id=current_user.id, following_id=target_user.id
                )
        return profile

    async def get_profiles_by_user_ids(
        self, session: AsyncSession, user_ids: List[int], current_user: Optional[UserSchema]
    ) -> List[ProfileSchema]:
        target_users = await self._user_service.get_users_by_ids(session=session, user_ids=user_ids)
        profiles = []
        following_map = {}

        if current_user:
            async with self._database_service.get_db() as session:
                following_user_ids = await self._get_following_ids(session=session, follower_id=current_user.id, following_ids=user_ids)
                following_map = {
                    following_id: True for following_id in following_user_ids
                }  # Create a map for efficient lookup

        for user_dto in target_users:
            profile = ProfileSchema(
                user_id=user_dto.id,
                username=user_dto.username,
                bio=user_dto.bio,
                image=user_dto.image_url,
                following=following_map.get(user_dto.id, False),  # Use the map
            )
            profiles.append(profile)
        return profiles

    async def follow_user(self, session: AsyncSession, username: str, current_user: UserSchema) -> None:
        if username == current_user.username:
            raise OwnProfileFollowingException()

        target_user = await self._user_service.get_user_by_username(session=session, username=username)

        async with self._database_service.get_db() as session:
            if await self._check_following(session=session, follower_id=current_user.id, following_id=target_user.id):
                raise ProfileAlreadyFollowedException()

            await self._create_follower_relationship(
                session=session, follower_id=current_user.id, following_id=target_user.id
            )

    async def unfollow_user(self, session: AsyncSession, username: str, current_user: UserSchema) -> None:
        if username == current_user.username:
            raise OwnProfileFollowingException()

        target_user = await self._user_service.get_user_by_username(session=session, username=username)
        async with self._database_service.get_db() as session:
            if not await self._check_following(session=session, follower_id=current_user.id, following_id=target_user.id):
                logger.exception("User not followed", username=username)
                raise ProfileNotFollowedFollowedException()
            await self._delete_follower_relationship(
                session=session, follower_id=current_user.id, following_id=target_user.id
            )

    #  helper methods for interacting with the database
    async def _check_following(self, session: AsyncSession, follower_id: int, following_id: int) -> bool:
        """Check if a user is following another user."""
        # Use a more explicit query
        query = select(exists().where(Follower.follower_id == follower_id, Follower.following_id == following_id))
        result = await session.execute(query)
        return result.scalar_one()

    async def _get_following_ids(self, session: AsyncSession, follower_id: int, following_ids: List[int]) -> List[int]:
        """Get the IDs of users that a given user is following from a list"""
        query = select(Follower.following_id).where(
            Follower.follower_id == follower_id, Follower.following_id.in_(following_ids)
        )
        result = await session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def _create_follower_relationship(self, session: AsyncSession, follower_id: int, following_id: int):
        """Create a follower relationship."""
        #  use core sqlachemy
        insert_stmt = insert(Follower).values(follower_id=follower_id, following_id=following_id)
        await session.execute(insert_stmt)

    async def _delete_follower_relationship(
        self, session: AsyncSession, follower_id: int, following_id: int
    ):
        """Delete a follower relationship."""
        #  use core sqlalchemy
        delete_stmt = delete(Follower).where(
            Follower.follower_id == follower_id, Follower.following_id == following_id
        )
        await session.execute(delete_stmt)
