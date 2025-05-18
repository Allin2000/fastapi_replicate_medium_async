from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# 请求相关模型 ===============================

class UserRegistrationData(BaseModel):
    email: str
    password: str
    username: str


class UserRegistrationRequest(BaseModel):
    user: UserRegistrationData


class UserLoginData(BaseModel):
    email: str
    password: str


class UserLoginRequest(BaseModel):
    user: UserLoginData


class UserUpdateData(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None


class UserUpdateRequest(BaseModel):
    user: UserUpdateData


# 内部数据库模型（用于 mapper） ===============================

class InternalUser(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str
    bio: str = ""
    image_url: Optional[str] = None
    created_at: datetime


# 通用用户展示字段 ===============================

class UserBase(BaseModel):
    email: str
    username: str
    bio: str = ""
    image: Optional[str] = None
    token: Optional[str] = None


class UserWithID(UserBase):
    id: int


# 响应相关模型 ===============================

class UserResponse(BaseModel):
    user: UserBase

    @classmethod
    def from_orm_with_token(cls, user_model, token: str) -> "UserResponse":
        return cls(user=UserBase(
            email=user_model.email,
            username=user_model.username,
            bio=user_model.bio,
            image=user_model.image_url,
            token=token,
        ))


class CurrentUserResponse(BaseModel):
    user: UserWithID

    @classmethod
    def from_orm_with_token(cls, user_model, token: str) -> "CurrentUserResponse":
        return cls(user=UserWithID(
            id=user_model.id,
            email=user_model.email,
            username=user_model.username,
            bio=user_model.bio,
            image=user_model.image_url,
            token=token,
        ))


class UpdatedUserResponse(BaseModel):
    user: UserWithID

    @classmethod
    def from_orm_with_token(cls, user_model, token: str) -> "UpdatedUserResponse":
        return cls(user=UserWithID(
            id=user_model.id,
            email=user_model.email,
            username=user_model.username,
            bio=user_model.bio,
            image=user_model.image_url,
            token=token,
        ))