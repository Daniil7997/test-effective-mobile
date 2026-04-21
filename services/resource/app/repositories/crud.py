import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.base import UserData, Posts
from app.schemas.pydantic_schemas import (PostData, PostsFromDB,
                                          User,
                                          DbUser,
                                          CreatePostReturn)
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.sqlalchemy import paginate


async def create_user(db: AsyncSession, data: User) -> DbUser:
    new_user = UserData(user_uuid=data.user_uuid,
                        username=data.username)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user, attribute_names=['created_at'])
    return DbUser(user_uuid=new_user.user_uuid,
                  username=new_user.username,
                  created_at=new_user.created_at)


async def create_post(db: AsyncSession,
                      data: PostData,
                      user_uuid: uuid.UUID) -> CreatePostReturn:
    new_post = Posts(title=data.title,
                     content=data.content,
                     user_uuid=user_uuid)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=['author'])
    return CreatePostReturn(content=new_post.content,
                            user_uuid=new_post.user_uuid,
                            author=new_post.author.username,
                            created_at=new_post.created_at)


async def read_posts(db: AsyncSession,
                     params: Params,) -> Page[PostsFromDB]:
    query = (select(Posts)
             .options(joinedload(Posts.author))
             .order_by(Posts.created_at.desc()))
    return await paginate(db,
                          query=query,
                          params=params,
                          transformer=lambda items: [
                              PostsFromDB.model_validate(i) for i in items
                              ])
