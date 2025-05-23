from datetime import datetime
from functools import partial

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


relationship = partial(relationship, lazy="raise")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    bio: Mapped[str]
    image_url: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime] = mapped_column(nullable=True)

    articles: Mapped[list["Article"]] = relationship(back_populates="author")


class Follower(Base):
    __tablename__ = "follower"

    # "follower" is a user who follows a user.
    follower_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    # "following" is a user who you follow.
    following_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    created_at: Mapped[datetime]


class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False, unique=True)
    title: Mapped[str]
    description: Mapped[str]
    body: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime] = mapped_column(nullable=True)

    author: Mapped["User"] = relationship(back_populates="articles")

    article_tags: Mapped[list["ArticleTag"]] = relationship(back_populates="article")


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tag: Mapped[str] = mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime]

    # ADD THIS: 定义反向关系，如果 ArticleTag 有一个指向 Tag 的关系
    article_tags_assoc: Mapped[list["ArticleTag"]] = relationship(back_populates="tag_obj")


class ArticleTag(Base):
    __tablename__ = "article_tag"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.id"), primary_key=True)
    created_at: Mapped[datetime]

        # ADD THIS: 定义 article 关系，连接到 Article 模型
    article: Mapped["Article"] = relationship(back_populates="article_tags")

    # ADD THIS: 定义 tag_obj 关系，连接到 Tag 模型 (名称与 service 层保持一致)
    tag_obj: Mapped["Tag"] = relationship(back_populates="article_tags_assoc")


class Favorite(Base):
    __tablename__ = "favorite"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime]


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    body: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime] = mapped_column(nullable=True)
