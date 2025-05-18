from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.core.date import convert_datetime_to_realworld

DEFAULT_ARTICLES_LIMIT = 20
DEFAULT_ARTICLES_OFFSET = 0

# 请求体（创建文章）
class CreateArticle(BaseModel):
    title: str
    description: str
    body: str
    tags: List[str] = Field(alias="tagList")


class CreateArticleRequest(BaseModel):
    article: CreateArticle


# 请求体（更新文章）
class UpdateArticle(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = Field(default=None, alias="tagList")


class UpdateArticleRequest(BaseModel):
    article: UpdateArticle


# 查询过滤器
class ArticlesFilters(BaseModel):
    tag: Optional[str] = None
    author: Optional[str] = None
    favorited: Optional[str] = None
    limit: int = Field(DEFAULT_ARTICLES_LIMIT, ge=1)
    offset: int = Field(DEFAULT_ARTICLES_OFFSET, ge=0)


# 作者信息
class ArticleAuthor(BaseModel):
    username: str
    bio: str = ""
    image: Optional[str] = None
    following: bool = False
    id: Optional[int] = None


# 单篇文章数据
class Article(BaseModel):
    id: int
    author_id: int
    slug: str
    title: str
    description: str
    body: str
    tags: List[str] = Field(alias="tagList")
    author: ArticleAuthor
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    favorited: bool = False
    favorites_count: int = Field(default=0, alias="favoritesCount")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: convert_datetime_to_realworld},
    )


# 响应格式（单篇）
class ArticleResponse(BaseModel):
    article: Article


# 响应格式（多篇）
class ArticlesFeedResponse(BaseModel):
    articles: List[Article]
    articles_count: int = Field(alias="articlesCount")

    model_config = ConfigDict(populate_by_name=True)


