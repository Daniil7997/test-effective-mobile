import asyncio

from app.db.database import async_session_factory
from app.repositories.crud import create_user, find_user_by_email
from app.schemas.pydantic_schemas import User
from app.models.users import UserRole


user = User(email='user@example.com',
            password='string')
admin = User(email='admin@example.com',
             password='admin')
msg = '\nТаблица auth_users заполнена данными для минимальной отработки\n'


async def seed():
    async with async_session_factory() as session:
        try:
            await create_user(db=session, user_data=user, role=UserRole.user)
            await create_user(db=session, user_data=admin, role=UserRole.admin)
            print(msg)
        finally:
            await session.close()


async def check_db():
    async with async_session_factory() as session:
        admin_exist = await find_user_by_email(db=session,
                                               user_email=admin.email)
        user_exist = await find_user_by_email(db=session,
                                              user_email=user.email)
        if admin_exist and user_exist:
            print(msg)
        else:
            await seed()


if __name__ == "__main__":
    asyncio.run(check_db())
