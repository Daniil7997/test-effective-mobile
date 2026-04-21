from datetime import datetime
import uuid

from pydantic import (BaseModel,
                      Field,
                      ConfigDict)


username_config = Field(max_length=20)
post_content_config = Field(max_length=750)
post_title_config = Field(max_length=30)


class User(BaseModel):
    user_uuid: uuid.UUID
    username: str = username_config


class RegisterUser(BaseModel):
    username: str


class DbUser(BaseModel):
    user_uuid: uuid.UUID
    username: str = username_config
    created_at: datetime


class AccessTokensPayload(BaseModel):
    sub: uuid.UUID
    iat: int
    exp: int
    role: str
    token_type: str


class PostData(BaseModel):
    title: str = post_title_config
    content: str = post_content_config


class CreatePostReturn(BaseModel):
    content: str = post_content_config
    user_uuid: uuid.UUID
    author: str
    created_at: datetime


class UserDataFromDB(BaseModel):
    username: str
    model_config = ConfigDict(from_attributes=True)


class PostsFromDB(BaseModel):
    user_uuid: uuid.UUID
    author: UserDataFromDB
    title: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
