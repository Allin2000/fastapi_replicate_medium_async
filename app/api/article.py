from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional,Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from starlette import status


from app.schemas.article import (
    Article as ArticleSchema,
    ArticleResponse,
    ArticlesFeedResponse,
    CreateArticle as CreateArticleDTO,
    UpdateArticle as UpdateArticleDTO,
)
from app.schemas.user import UserWithID
from app.services.article import ArticleService
from app.services.favorite import FavoriteService
from app.services.article_tag import ArticleTagService
from app.core.dep import get_db_session
from app.core.dep import get_current_user, get_current_user_or_none,get_Article_service,get_FavoriteService,get_ArticleTagService

router = APIRouter()



@router.get("/feed",response_model=ArticlesFeedResponse)
async def get_article_feed(
    session:AsyncSession=Depends(get_db_session),
    current_user:UserWithID=Depends(get_current_user),
    article_service:ArticleService=Depends(get_Article_service) ,
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
) -> dict :
    """
    Get article feed from following users.
    """
    articles = await article_service.list_by_followings_v2(
        session=session, user_id=current_user.id, limit=limit, offset=offset
    )
    articles_count = await article_service.count_by_followings(session=session, user_id=current_user.id)
    return ArticlesFeedResponse(articles=articles, articlesCount=articles_count)


@router.get("", response_model=ArticlesFeedResponse)
async def get_global_article_feed(
   session:AsyncSession=Depends(get_db_session),
    current_user:Optional[UserWithID]=Depends(get_current_user_or_none),
    article_service:ArticleService=Depends(get_Article_service) ,
    tag: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    favorited: Optional[str] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
) -> ArticlesFeedResponse:
    """
    Get global article feed.
    """
    user_id = current_user.id if current_user else None
    articles = await article_service.list_by_filters_v2(
        session=session,
        user_id=user_id,
        tag=tag,
        author=author,
        favorited=favorited,
        limit=limit,
        offset=offset,
    )
    articles_count = await article_service.count_by_filters(
        session=session, tag=tag, author=author, favorited=favorited
    )
    return ArticlesFeedResponse(articles=articles, articlesCount=articles_count)


@router.post("", response_model=ArticleResponse)
async def create_article(
    payload: CreateArticleDTO,
  session:AsyncSession=Depends(get_db_session),
    current_user:UserWithID=Depends(get_current_user),
      article_service:ArticleService=Depends(get_Article_service) ,
 article_tag_service:ArticleTagService=Depends(get_ArticleTagService)

) -> ArticleResponse:
    """
    Create new article.
    """
    article = await article_service.add(session=session, author_id=current_user.id, create_item=payload)
    # 创建文章后需要处理标签

    
    await article_tag_service.add_many(session=session, article_id=article.id, tags=payload.tags)
    article_response = await article_service._build_article_schema_with_author(session, article)
    return ArticleResponse(article=article_response)


@router.put("/{slug}", response_model=ArticleResponse)
async def update_article(
    slug: str,
    payload: UpdateArticleDTO,
 session:AsyncSession=Depends(get_db_session),
   current_user:UserWithID=Depends(get_current_user),
     article_service:ArticleService=Depends(get_Article_service) ,
) -> ArticleResponse:
    """
    Update an article.
    """
 
    existing_article = await article_service.get_by_slug(session=session, slug=slug)
    if existing_article.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this article")

    article = await article_service.update_by_slug(session=session, slug=slug, update_item=payload)
    # 更新文章后需要更新标签
    from app.services.article_tag import ArticleTagService
    article_tag_service = ArticleTagService()
    if payload.tags is not None:
        # 先删除旧的标签关联 (需要根据你的具体实现调整)
        # await session.execute(delete(ArticleTag).where(ArticleTag.article_id == article.id))
        # 再添加新的标签
        await article_tag_service.add_many(session=session, article_id=article.id, tags=payload.tags)
    article_response = await article_service._build_article_schema_with_author(session, article)
    return ArticleResponse(article=article_response)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    slug: str,
  session:AsyncSession=Depends(get_db_session),
   current_user:UserWithID=Depends(get_current_user),
    article_service:ArticleService=Depends(get_Article_service) ,
) -> None:
    """
    Delete an article by slug.
    """

    article = await article_service.get_by_slug(session=session, slug=slug)
    if article.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this article")
    await article_service.delete_by_slug(session=session, slug=slug)


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
   session:AsyncSession=Depends(get_db_session),
   current_user:UserWithID=Depends(get_current_user),
    article_service:ArticleService=Depends(get_Article_service) ,
) -> ArticleResponse:
    """
    Get new article by slug.
    """
    article = await article_service.get_by_slug(session=session, slug=slug)
    # 需要根据 current_user 信息完善 ArticleSchema 的 following 和 favorited 字段
    article_response = await article_service._build_article_schema_with_author(session, article)
    if current_user:
        # 这里需要查询当前用户是否关注了文章作者，以及是否收藏了该文章
        from app.services.follower import FollowerService
        from app.services.favorite import FavoriteService
        follower_service = FollowerService()
        favorite_service = FavoriteService()
        is_following = await follower_service.exists(session, current_user.id, article.author_id)
        is_favorited = await favorite_service.exists(session, current_user.id, article.id)
        article_response.author.following = is_following
        article_response.favorited = is_favorited
    return ArticleResponse(article=article_response)

@router.post("/{slug}/favorite", response_model=ArticleResponse)
async def favorite_article(
    slug: str,
  session:AsyncSession=Depends(get_db_session),
   current_user:UserWithID=Depends(get_current_user),
    article_service:ArticleService=Depends(get_Article_service) ,
    favorite_service:FavoriteService=Depends(get_FavoriteService)
) -> ArticleResponse:
    """
    Favorite an article.
    """
    article = await article_service.get_by_slug(session=session, slug=slug)

    if not await favorite_service.exists(session, current_user.id, article.id):
        await favorite_service.create(session, article.id, current_user.id)
    article_response = await article_service._build_article_schema_with_author(session, article)
    article_response.favorited = True
    article_response.favoritesCount = await favorite_service.count(session, article.id)
    return ArticleResponse(article=article_response)


@router.delete("/{slug}/favorite", response_model=ArticleResponse)
async def unfavorite_article(
    slug: str,
 session:AsyncSession=Depends(get_db_session),
   current_user:Optional[UserWithID]=Depends(get_current_user_or_none),
    article_service:ArticleService=Depends(get_Article_service) ,
        favorite_service:FavoriteService=Depends(get_FavoriteService)
) -> ArticleResponse:
    """
    Unfavorite an article.
    """
    article = await article_service.get_by_slug(session=session, slug=slug)
    if await favorite_service.exists(session, current_user.id, article.id):
        await favorite_service.delete(session, article.id, current_user.id)
    article_response = await article_service._build_article_schema_with_author(session, article)
    article_response.favorited = False
    article_response.favoritesCount = await favorite_service.count(session, article.id)
    return ArticleResponse(article=article_response)