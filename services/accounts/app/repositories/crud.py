import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from app.core.security import hash_password
from app.models.users import AuthUsers, UserRole
from app.schemas.pydantic_schemas import User, DbUserData


async def create_user(db: AsyncSession,
                      user_data: User,
                      role: UserRole = UserRole.user
                      ) -> DbUserData:
    hashed_password = hash_password(user_data.password)
    db_user = AuthUsers(email=user_data.email, password=hashed_password)
    db.add(db_user)
    await db.commit()
    return DbUserData(user_uuid=db_user.user_uuid,
                      email=db_user.email,
                      password=db_user.password,
                      role=db_user.role)


async def find_user_by_email(db: AsyncSession,
                             user_email: EmailStr) -> DbUserData | None:
    select_column = [AuthUsers.user_uuid,
                     AuthUsers.email,
                     AuthUsers.password,
                     AuthUsers.role]
    stmt = select(*select_column).where(AuthUsers.email == user_email,
                                        AuthUsers.is_active)
    result = await db.execute(stmt)
    user_db_data = result.one_or_none()
    if not user_db_data:
        return None
    return DbUserData(user_uuid=user_db_data.user_uuid,
                      email=user_db_data.email,
                      password=user_db_data.password,
                      role=user_db_data.role)


async def find_user_by_uuid(db: AsyncSession,
                            user_uuid: uuid.UUID) -> DbUserData | None:
    select_column = [AuthUsers.user_uuid,
                     AuthUsers.email,
                     AuthUsers.password,
                     AuthUsers.role]
    stmt = select(*select_column).where(AuthUsers.user_uuid == user_uuid,
                                        AuthUsers.is_active)
    result = await db.execute(stmt)
    user_db_data = result.one_or_none()
    if not user_db_data:
        return None
    return DbUserData(user_uuid=user_db_data.user_uuid,
                      email=user_db_data.email,
                      password=user_db_data.password,
                      role=user_db_data.role)


@asynccontextmanager
async def change_user_data(
    db: AsyncSession,
    user_uuid: uuid.UUID
) -> AsyncGenerator[AuthUsers | None, None]:
    stmt = select(AuthUsers).where(AuthUsers.user_uuid == user_uuid,
                                   AuthUsers.is_active)
    result = await db.execute(stmt)
    user_db_data = result.one_or_none()
    if not user_db_data:
        yield None
    try:
        yield user_db_data
        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def delete_user(db: AsyncSession, user_email: EmailStr) -> bool:
    stmt = delete(AuthUsers).where(AuthUsers.email == user_email)
    await db.execute(stmt)
    await db.commit()
    return True
