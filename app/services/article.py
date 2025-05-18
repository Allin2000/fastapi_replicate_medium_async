from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import delete, exists, func, insert, select, true, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.exception import ArticleNotFoundException
from app.core.slug import (
    get_slug_unique_part,
    make_slug_from_title,
    make_slug_from_title_and_code,
)
from app.sqlmodel.alembic_model import Article, ArticleTag, Favorite, Follower, Tag, User
from app.schemas.article import Article as ArticleSchema, ArticleAuthor,CreateArticle,UpdateArticle


# Aliases for the models if needed.
FavoriteAlias = aliased(Favorite)


class ArticleService:
    """Service for Article model, without DTO conversion."""

    async def add(
        self, session: AsyncSession, author_id: int, create_item: CreateArticle
    ) -> Article:
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
        return result.scalar_one()

    async def get_by_slug_or_none(
        self, session: AsyncSession, slug: str
    ) -> Optional[Article]:
        slug_unique_part = get_slug_unique_part(slug=slug)
        query = select(Article).where(
            (Article.slug == slug) | (Article.slug.contains(slug_unique_part))
        )
        return await session.scalar(query)

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Article:
        slug_unique_part = get_slug_unique_part(slug=slug)
        query = select(Article).where(
            (Article.slug == slug) | (Article.slug.contains(slug_unique_part))
        )
        article = await session.scalar(query)
        if not article:
            raise ArticleNotFoundException()
        return article

    async def delete_by_slug(self, session: AsyncSession, slug: str) -> None:
        query = delete(Article).where(Article.slug == slug)
        await session.execute(query)

    async def update_by_slug(
        self, session: AsyncSession, slug: str, update_item: UpdateArticle
    ) -> Article:
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
        return result.scalar_one()

    async def list_by_followings(
        self, session: AsyncSession, user_id: int, limit: int, offset: int
    ) -> List[ArticleSchema]:
        query = (
            select(
                Article.id,
                Article.author_id,
                Article.slug,
                Article.title,
                Article.description,
                Article.body,
                Article.created_at,
                Article.updated_at,
                User.username,
                User.bio,
                User.image_url,
            )
            .join(
                Follower,
                (Follower.following_id == Article.author_id) & (Follower.follower_id == user_id),
            )
            .join(User, (User.id == Article.author_id))
            .order_by(Article.created_at)
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        articles = result.all()
        return [self._build_article_schema(article) for article in articles]

    async def list_by_followings_v2(
        self, session: AsyncSession, user_id: int, limit: int, offset: int
    ) -> List[ArticleSchema]:
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
        articles = result.all()
        return [self._build_article_schema(article) for article in articles]

    async def list_by_filters(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
    ) -> List[ArticleSchema]:
        query = (
            select(
                Article.id,
                Article.author_id,
                Article.slug,
                Article.title,
                Article.description,
                Article.body,
                Article.created_at,
                Article.updated_at,
            )
            .order_by(Article.created_at)
            .limit(limit)
            .offset(offset)
        )

        if tag:
            query = query.join(
                ArticleTag, (Article.id == ArticleTag.article_id)
            ).where(
                ArticleTag.tag_id == select(Tag.id).where(Tag.tag == tag).scalar_subquery()
            )

        if author:
            query = query.join(User, (User.id == Article.author_id)).where(User.username == author)

        if favorited:
            query = query.join(Favorite, (Favorite.article_id == Article.id)).where(
                Favorite.user_id == select(User.id).where(User.username == favorited).scalar_subquery()
            )

        result = await session.execute(query)
        articles = result.all()
        return [await self._build_article_schema_with_author(session, article) for article in articles]

    async def list_by_filters_v2(
        self,
        session: AsyncSession,
        user_id: Optional[int],
        limit: int,
        offset: int,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
    ) -> List[ArticleSchema]:
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
                exists()
                .where(
                    (Follower.follower_id == user_id) & (Follower.following_id == Article.author_id)
                )
                .label("following"),
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
            .outerjoin(User, Article.author_id == User.id)
            .outerjoin(ArticleTag, Article.id == ArticleTag.article_id)
            .outerjoin(FavoriteAlias, FavoriteAlias.article_id == Article.id)
            .outerjoin(Tag, Tag.id == ArticleTag.tag_id)
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
        articles = result.all()
        return [self._build_article_schema(article) for article in articles]

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
            query = query.join(
                ArticleTag, (Article.id == ArticleTag.article_id)
            ).where(
                ArticleTag.tag_id == select(Tag.id).where(Tag.tag == tag).scalar_subquery()
            )

        if author:
            query = query.join(User, (User.id == Article.author_id)).where(User.username == author)

        if favorited:
            query = query.join(Favorite, (Favorite.article_id == Article.id)).where(
                Favorite.user_id == select(User.id).where(User.username == favorited).scalar_subquery()
            )

        result = await session.execute(query)
        return result.scalar_one()

    def _build_article_schema(self, res: Any) -> ArticleSchema:
        return ArticleSchema(
            id=res.id,
            slug=res.slug,
            title=res.title,
            description=res.description,
            body=res.body,
            tagList=res.tags.split(", ") if res.tags else [],
            author=ArticleAuthor(
                username=res.username,
                bio=res.bio,
                image=res.image_url,
                following=res.following,
            ),
            createdAt=res.created_at,
            updatedAt=res.updated_at,
            favorited=res.favorited,
            favoritesCount=res.favorites_count,
        )

    async def _build_article_schema_with_author(self, session: AsyncSession, article: Article) -> ArticleSchema:
        author = await session.scalar(select(User).where(User.id == article.author_id))
        tags = await session.scalars(
            select(Tag)
            .join(ArticleTag, (ArticleTag.tag_id == Tag.id) & (ArticleTag.article_id == article.id))
        )
        favorites_count = await session.scalar(select(func.count(Favorite.article_id)).where(Favorite.article_id == article.id)) or 0
        favorited = False  # 需要用户 ID 才能判断是否已收藏，这里暂时设置为 False

        return ArticleSchema(
            id=article.id,
            slug=article.slug,
            title=article.title,
            description=article.description,
            body=article.body,
            tagList=[tag.tag for tag in tags],
            author=ArticleAuthor(
                username=author.username,
                bio=author.bio,
                image=author.image_url,
                following=False,  # 需要用户 ID 才能判断是否已关注，这里暂时设置为 False
            ),
            createdAt=article.created_at,
            updatedAt=article.updated_at,
            favorited=favorited,
            favoritesCount=favorites_count,
        )
