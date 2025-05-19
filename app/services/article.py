from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import delete, exists, func, insert, select, true, update, desc # Import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload # Import joinedload

from app.core.exception import ArticleNotFoundException
from app.core.slug import (
    get_slug_unique_part,
    make_slug_from_title,
    make_slug_from_title_and_code,
)
from app.sqlmodel.alembic_model import Article, ArticleTag, Favorite, Follower, Tag, User

# Import your defined DTOs
from app.schemas.article import (
    ArticleRecordDTO,
    CreateArticleDTO,
    UpdateArticleDTO,
    ArticleAuthorDTO,
    ArticleDTO,
    ArticlesFeedDTO,
)

# Aliases for the models if needed.
FavoriteAlias = aliased(Favorite)


class ArticleService:

    # Helper method to build ArticleDTO from a SQLAlchemy row or model
    # This centralizes the DTO creation logic
    async def _build_article_dto_from_db_result(
        self, session: AsyncSession, db_result: Any, user_id: Optional[int] = None
    ) -> ArticleDTO:
        """
        Builds an ArticleDTO from a SQLAlchemy row object or an Article model instance.
        Fetches additional details (author, tags, favorites) if not present in the row.
        """
        article_id = getattr(db_result, 'id', None)
        author_id = getattr(db_result, 'author_id', None)

        # Initialize common fields
        article_dto_data = {
            "id": article_id,
            "slug": getattr(db_result, 'slug', None),
            "title": getattr(db_result, 'title', None),
            "description": getattr(db_result, 'description', None),
            "body": getattr(db_result, 'body', None),
            "created_at": getattr(db_result, 'created_at', None),
            "updated_at": getattr(db_result, 'updated_at', None),
        }

        # --- Author details ---
        author_dto_data = {
            "username": getattr(db_result, 'username', ""),
            "bio": getattr(db_result, 'bio', ""),
            "image": getattr(db_result, 'image_url', None),
            "following": getattr(db_result, 'following', False),
            "id": getattr(db_result, 'user_id', None),
        }

        # If author data is missing from row (e.g., from ArticleRecordDTO creation)
        if not author_dto_data["username"] and author_id:
            author_model = await session.scalar(select(User).where(User.id == author_id))
            if author_model:
                author_dto_data["username"] = author_model.username
                author_dto_data["bio"] = author_model.bio
                author_dto_data["image"] = author_model.image_url
                author_dto_data["id"] = author_model.id
                if user_id: # Check following only if user_id is provided
                    following_check = await session.scalar(
                        select(exists().where((Follower.follower_id == user_id) & (Follower.following_id == author_model.id)))
                    )
                    author_dto_data["following"] = following_check if following_check is not None else False

        article_dto_data["author"] = ArticleAuthorDTO(**author_dto_data)

        # --- Tags ---
        tags_list = getattr(db_result, 'tags', None)
        if tags_list is None and article_id: # If tags not in row, query them
            tags_models = await session.scalars(
                select(Tag)
                .join(ArticleTag, (ArticleTag.tag_id == Tag.id) & (ArticleTag.article_id == article_id))
            )
            tags_list = [tag.tag for tag in tags_models.all()]
        elif isinstance(tags_list, str): # Handle comma-separated string from func.string_agg
            tags_list = [tag.strip() for tag in tags_list.split(",")] if tags_list else []
        else: # Default to empty list
            tags_list = []
        article_dto_data["tags"] = tags_list

        # --- Favorites ---
        article_dto_data["favorites_count"] = getattr(db_result, 'favorites_count', 0)
        article_dto_data["favorited"] = getattr(db_result, 'favorited', False)
        
        # If favorited/favorites_count not in row, query them
        if (article_dto_data["favorites_count"] == 0 and not article_dto_data["favorited"]) and article_id:
             favorites_count_query = await session.scalar(select(func.count(Favorite.article_id)).where(Favorite.article_id == article_id))
             article_dto_data["favorites_count"] = favorites_count_query or 0
             if user_id:
                 favorited_check = await session.scalar(
                     select(exists().where((Favorite.user_id == user_id) & (Favorite.article_id == article_id)))
                 )
                 article_dto_data["favorited"] = favorited_check if favorited_check is not None else False


        return ArticleDTO(**article_dto_data)


    async def add(
        self, session: AsyncSession, author_id: int, create_item: CreateArticleDTO
    ) -> ArticleDTO: # Returns full ArticleDTO
        query = (
            insert(Article)
            .values(
                author_id=author_id,
                slug=make_slug_from_title(title=create_item.title),
                title=create_item.title,
                description=create_item.description,
                body=create_item.body,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            .returning(Article)
        )
        result = await session.execute(query)
        article_model = result.scalar_one()

        # To return a full ArticleDTO, we need more data than just the basic Article record.
        # This will involve fetching author, tags, etc.
        # This is a good place to call the comprehensive helper.
        return await self._build_article_dto_from_db_result(session, article_model, user_id=None) # user_id=None for initial add

    async def get_by_slug_or_none(
        self, session: AsyncSession, slug: str
    ) -> Optional[ArticleRecordDTO]: # Returns ArticleRecordDTO for simple lookup
        slug_unique_part = get_slug_unique_part(slug=slug)
        query = select(Article).where(
            (Article.slug == slug) | (Article.slug.contains(slug_unique_part))
        )
        article = await session.scalar(query)
        if article:
            return ArticleRecordDTO(
                id=article.id,
                author_id=article.author_id,
                slug=article.slug,
                title=article.title,
                description=article.description,
                body=article.body,
                created_at=article.created_at,
                updated_at=article.updated_at,
            )
        return None

    async def get_by_slug(self, session: AsyncSession, slug: str) -> ArticleDTO: # Returns full ArticleDTO
        slug_unique_part = get_slug_unique_part(slug=slug)
        query = select(Article).where(
            (Article.slug == slug) | (Article.slug.contains(slug_unique_part))
        )
        article = await session.scalar(query)
        if not article:
            raise ArticleNotFoundException()
        
        # Return full ArticleDTO for a single lookup by slug, assuming more details are needed
        return await self._build_article_dto_from_db_result(session, article, user_id=None)


    async def delete_by_slug(self, session: AsyncSession, slug: str) -> None:
        query = delete(Article).where(Article.slug == slug)
        await session.execute(query)

    async def update_by_slug(
        self, session: AsyncSession, slug: str, update_item: UpdateArticleDTO
    ) -> ArticleDTO: # Returns full ArticleDTO
        query = (
            update(Article)
            .where(Article.slug == slug)
            .values(updated_at=datetime.now())
            .returning(Article)
        )
        if update_item.title is not None:
            updated_slug = make_slug_from_title_and_code(
                title=update_item.title, code=get_slug_unique_part(slug=slug)
            )
            query = query.values(title=update_item.title, slug=updated_slug)
        if update_item.description is not None:
            query = query.values(description=update_item.description)
        if update_item.body is not None:
            query = query.values(body=update_item.body)

        result = await session.execute(query)
        article_model = result.scalar_one()

        # Handle tags update
        if update_item.tags is not None:
            # 1. Delete existing ArticleTag entries for this article
            await session.execute(delete(ArticleTag).where(ArticleTag.article_id == article_model.id))
            
            # 2. Find or create new tags and link them
            tag_objects = []
            if update_item.tags:
                # Insert new tags if they don't exist, and get their IDs
                insert_tag_query = (
                    insert(Tag)
                    .on_conflict_do_nothing(index_elements=[Tag.tag]) # Assuming 'tag' column is unique
                    .values([{"tag": tag, "created_at": datetime.now()} for tag in update_item.tags])
                    .returning(Tag)
                )
                # Fetch existing tags as well if they were not inserted (due to on_conflict_do_nothing)
                # Need to select tags based on the list of tags
                existing_tags_query = select(Tag).where(Tag.tag.in_(update_item.tags))
                
                inserted_tags_result = await session.execute(insert_tag_query)
                inserted_tags = inserted_tags_result.scalars().all()
                
                existing_tags_result = await session.execute(existing_tags_query)
                existing_tags = existing_tags_result.scalars().all()

                # Combine all tags (inserted + existing)
                all_tags_map = {t.tag: t for t in inserted_tags + existing_tags}
                tag_objects = [all_tags_map[tag] for tag in update_item.tags if tag in all_tags_map]


            # 3. Create new ArticleTag links
            if tag_objects:
                link_values = [
                    {"article_id": article_model.id, "tag_id": tag.id, "created_at": datetime.now()}
                    for tag in tag_objects
                ]
                insert_link_query = insert(ArticleTag).values(link_values)
                await session.execute(insert_link_query)
            
            # Commit the tag changes
            await session.commit()


        # Return full ArticleDTO
        return await self._build_article_dto_from_db_result(session, article_model, user_id=None)


    async def list_by_followings(
        self, session: AsyncSession, user_id: int, limit: int, offset: int
    ) -> ArticlesFeedDTO: # Changed to return ArticlesFeedDTO
        # This query needs to be more comprehensive to populate ArticleDTO directly
        # I'm adapting it to match the structure of list_by_followings_v2
        query = (
            select(
                Article.id.label("id"),
                Article.author_id.label("author_id"),
                Article.slug.label("slug"),
                Article.title.label("title"),
                Article.description.label("description"),
                Article.body.label("body"),
                Article.created_at.label("created_at"),
                Article.updated_at.label("updated_at"),
                User.id.label("user_id"),
                User.username.label("username"),
                User.bio.label("bio"),
                User.image_url.label("image_url"),
                true().label("following"), # Assuming 'true' because these are user's followings
                # Subquery for favorites count.
                select(func.count(Favorite.article_id))
                .where(Favorite.article_id == Article.id)
                .scalar_subquery()
                .label("favorites_count"),
                # Subquery to check if favorited by user with id `user_id`.
                exists()
                .where((Favorite.user_id == user_id) & (Favorite.article_id == Article.id))
                .label("favorited"),
                # Concatenate tags.
                func.string_agg(Tag.tag, ", ").label("tags"),
            )
            .join(
                Follower,
                (Follower.following_id == Article.author_id) & (Follower.follower_id == user_id),
            )
            .join(User, (User.id == Article.author_id))
            .outerjoin(ArticleTag, Article.id == ArticleTag.article_id) # Ensure tags are joined
            .outerjoin(Tag, Tag.id == ArticleTag.tag_id) # Ensure tags are joined
            .group_by( # Group by all selected non-aggregated columns
                Article.id,
                Article.author_id,
                Article.slug,
                Article.title,
                Article.description,
                Article.body,
                Article.created_at,
                Article.updated_at,
                User.id,
                User.username,
                User.bio,
                User.image_url,
            )
            .order_by(desc(Article.created_at)) # Using desc from sqlalchemy
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        raw_articles = result.all()

        articles_dto = [
            await self._build_article_dto_from_db_result(session, row, user_id)
            for row in raw_articles
        ]
        
        total_count = await self.count_by_followings(session, user_id)
        return ArticlesFeedDTO(articles=articles_dto, articles_count=total_count)


    async def list_by_followings_v2(
        self, session: AsyncSession, user_id: int, limit: int, offset: int
    ) -> ArticlesFeedDTO: # Returns ArticlesFeedDTO
        query = (
            select(
                Article.id.label("id"),
                Article.author_id.label("author_id"),
                Article.slug.label("slug"),
                Article.title.label("title"),
                Article.description.label("description"),
                Article.body.label("body"),
                Article.created_at.label("created_at"),
                Article.updated_at.label("updated_at"),
                User.id.label("user_id"),
                User.username.label("username"),
                User.bio.label("bio"),
                User.email.label("email"),
                User.image_url.label("image_url"),
                true().label("following"),
                # Subquery for favorites count.
                select(func.count(Favorite.article_id))
                .where(Favorite.article_id == Article.id)
                .scalar_subquery()
                .label("favorites_count"),
                # Subquery to check if favorited by user with id `user_id`.
                exists()
                .where((Favorite.user_id == user_id) & (Favorite.article_id == Article.id))
                .label("favorited"),
                # Concatenate tags.
                func.string_agg(Tag.tag, ", ").label("tags"),
            )
            .join(User, Article.author_id == User.id)
            .join(ArticleTag, Article.id == ArticleTag.article_id)
            .join(Tag, Tag.id == ArticleTag.tag_id)
            .filter(
                User.id.in_(
                    select(Follower.following_id).where(Follower.follower_id == user_id).scalar_subquery()
                )
            )
            .group_by(
                Article.id,
                Article.author_id,
                Article.slug,
                Article.title,
                Article.description,
                Article.body,
                Article.created_at,
                Article.updated_at,
                User.id,
                User.username,
                User.bio,
                User.email,
                User.image_url,
            )
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        raw_articles = result.all()
        
        articles_dto = [
            await self._build_article_dto_from_db_result(session, row, user_id)
            for row in raw_articles
        ]
        
        total_count = await self.count_by_followings(session, user_id)
        return ArticlesFeedDTO(articles=articles_dto, articles_count=total_count)


    async def list_by_filters(
        self,
        session: AsyncSession, # Add session here
        limit: int = 20, # Use default from DTO
        offset: int = 0, # Use default from DTO
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None, # Consistent with DTO
    ) -> ArticlesFeedDTO: # Returns ArticlesFeedDTO
        # This old style query only returns basic Article fields.
        # We need to extend it or do additional queries to get full DTO data.
        # I'll extend it to match list_by_filters_v2 to be more efficient.
        query = (
            select(
                Article.id.label("id"),
                Article.author_id.label("author_id"),
                Article.slug.label("slug"),
                Article.title.label("title"),
                Article.description.label("description"),
                Article.body.label("body"),
                Article.created_at.label("created_at"),
                Article.updated_at.label("updated_at"),
                User.id.label("user_id"),
                User.username.label("username"),
                User.bio.label("bio"),
                User.image_url.label("image_url"),
                # For filters, following/favorited status depends on a potential user_id.
                # Assuming no specific user is logged in for this method, these will be False.
                # Or, you might pass an optional user_id to this method if needed.
                # For now, will set to False or determine based on `user_id` if passed.
                false().label("following"), # Set to false if no user_id is passed or not explicitly checking
                select(func.count(Favorite.article_id))
                .where(Favorite.article_id == Article.id)
                .scalar_subquery()
                .label("favorites_count"),
                false().label("favorited"), # Set to false if no user_id is passed or not explicitly checking
                func.string_agg(Tag.tag, ", ").label("tags"),
            )
            .outerjoin(User, Article.author_id == User.id)
            .outerjoin(ArticleTag, Article.id == ArticleTag.article_id)
            .outerjoin(Tag, Tag.id == ArticleTag.tag_id)
            .outerjoin(FavoriteAlias, FavoriteAlias.article_id == Article.id)
            .group_by(
                Article.id,
                Article.author_id,
                Article.slug,
                Article.title,
                Article.description,
                Article.body,
                Article.created_at,
                Article.updated_at,
                User.id,
                User.username,
                User.bio,
                User.image_url,
            )
            .order_by(desc(Article.created_at))
            .limit(limit)
            .offset(offset)
        )

        conditions = []
        if tag:
            # Note: For tag filtering, if multiple tags per article, you might need `having` clause
            # or a subquery to filter on aggregated tags if the join produces duplicates.
            # Keeping it simple based on your original where clause logic on Tag.tag
            conditions.append(Tag.tag == tag)

        if author:
            conditions.append(User.username == author)

        if favorited:
            subquery = select(User.id).where(User.username == favorited).scalar_subquery()
            conditions.append(FavoriteAlias.user_id == subquery)

        if conditions:
            # Apply all conditions to the query
            query = query.where(*conditions)

        result = await session.execute(query)
        raw_articles = result.all()

        articles_dto = [
            await self._build_article_dto_from_db_result(session, row, user_id=None) # Pass user_id if available for 'favorited'/'following'
            for row in raw_articles
        ]

        total_count = await self.count_by_filters(session, tag, author, favorited)
        return ArticlesFeedDTO(articles=articles_dto, articles_count=total_count)


    async def list_by_filters_v2(
        self,
        session: AsyncSession,
        user_id: Optional[int],
        limit: int,
        offset: int,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
    ) -> ArticlesFeedDTO: # Returns ArticlesFeedDTO
        query = (
            select(
                Article.id.label("id"),
                Article.author_id.label("author_id"),
                Article.slug.label("slug"),
                Article.title.label("title"),
                Article.description.label("description"),
                Article.body.label("body"),
                Article.created_at.label("created_at"),
                Article.updated_at.label("updated_at"),
                User.id.label("user_id"),
                User.username.label("username"),
                User.bio.label("bio"),
                User.image_url.label("image_url"),
                exists()
                .where(
                    (Follower.follower_id == user_id) & (Follower.following_id == Article.author_id)
                )
                .label("following") if user_id else false().label("following"), # Conditionally check or set to false
                # Subquery for favorites count.
                select(func.count(Favorite.article_id))
                .where(Favorite.article_id == Article.id)
                .scalar_subquery()
                .label("favorites_count"),
                # Subquery to check if favorited by user with id `user_id`.
                exists()
                .where((Favorite.user_id == user_id) & (Favorite.article_id == Article.id))
                .label("favorited") if user_id else false().label("favorited"), # Conditionally check or set to false
                # Concatenate tags.
                func.string_agg(Tag.tag, ", ").label("tags"),
            )
            .outerjoin(User, Article.author_id == User.id)
            .outerjoin(ArticleTag, Article.id == ArticleTag.article_id)
            .outerjoin(Tag, Tag.id == ArticleTag.tag_id)
            .outerjoin(FavoriteAlias, FavoriteAlias.article_id == Article.id)
            .group_by(
                Article.id,
                Article.author_id,
                Article.slug,
                Article.title,
                Article.description,
                Article.body,
                Article.created_at,
                Article.updated_at,
                User.id,
                User.username,
                User.bio,
                User.image_url,
            )
            .limit(limit)
            .offset(offset)
        )

        conditions = []
        if author:
            conditions.append(User.username == author)
        if tag:
            conditions.append(Tag.tag == tag)
        if favorited:
            subquery = select(User.id).where(User.username == favorited).scalar_subquery()
            conditions.append(FavoriteAlias.user_id == subquery)

        if conditions:
            query = query.where(*conditions)

        result = await session.execute(query)
        raw_articles = result.all()

        articles_dto = [
            await self._build_article_dto_from_db_result(session, row, user_id)
            for row in raw_articles
        ]
        
        total_count = await self.count_by_filters(session, tag, author, favorited)
        return ArticlesFeedDTO(articles=articles_dto, articles_count=total_count)


    async def count_by_followings(self, session: AsyncSession, user_id: int) -> int:
        query = select(func.count(Article.id)).join(
            Follower, (Follower.following_id == Article.author_id) & (Follower.follower_id == user_id)
        )
        result = await session.execute(query)
        return result.scalar_one()

    async def count_by_filters(
        self,
        session: AsyncSession,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
    ) -> int:
        query = select(func.count(Article.id))

        if tag:
            # Correct join on ORM models
            query = query.join(ArticleTag, Article.id == ArticleTag.article_id).join(Tag, ArticleTag.tag_id == Tag.id).where(Tag.tag == tag)

        if author:
            query = query.join(User, (User.id == Article.author_id)).where(User.username == author)

        if favorited:
            query = query.join(Favorite, (Favorite.article_id == Article.id)).where(
                Favorite.user_id == select(User.id).where(User.username == favorited).scalar_subquery()
            )

        result = await session.execute(query)
        return result.scalar_one()

    # Old helper methods are replaced by _build_article_dto_from_db_result
    # def _build_article_schema(self, res: Any) -> ArticleSchema: ...
    # async def _build_article_schema_with_author(self, session: AsyncSession, article: Article) -> ArticleSchema: ...