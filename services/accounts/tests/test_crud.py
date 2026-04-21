import pytest
import uuid

from app.core.security import hash_password
from app.repositories.crud import (create_user,
                                   change_user_data,
                                   delete_user,
                                   find_user_by_email,
                                   find_user_by_uuid)
from app.schemas.pydantic_schemas import DbUserData
from tests.utils_for_tests import test_users


@pytest.mark.crud
@pytest.mark.asyncio
async def test_create_user(global_sessionmaker):
    async with global_sessionmaker() as session:
        user = test_users[0]
        response = await create_user(db=session, user_data=user)
    assert isinstance(response, DbUserData)
    assert isinstance(response.user_uuid, uuid.UUID)
    assert response.email == user.email
    assert response.password != user.password


@pytest.mark.crud
@pytest.mark.asyncio
async def test_find_user_by_email(global_sessionmaker):
    async with global_sessionmaker() as session:
        user = test_users[0]
        await create_user(db=session, user_data=user)
        response = await find_user_by_email(db=session,
                                            user_email=user.email)

    assert isinstance(response, DbUserData)
    assert isinstance(response.user_uuid, uuid.UUID)
    assert response.email == user.email


@pytest.mark.crud
@pytest.mark.asyncio
async def test_find_user_by_email__not_found(global_sessionmaker):
    async with global_sessionmaker() as session:
        user = test_users[0]
        response = await find_user_by_email(db=session,
                                            user_email=user.email)
    assert response is None


@pytest.mark.crud
@pytest.mark.asyncio
async def test_find_user_by_uuid(global_sessionmaker):
    async with global_sessionmaker() as session:
        user = test_users[0]
        db_user = await create_user(db=session, user_data=user)
        response = await find_user_by_uuid(db=session,
                                           user_uuid=db_user.user_uuid)
    assert isinstance(response, DbUserData)
    assert isinstance(response.user_uuid, uuid.UUID)
    assert response.email == user.email


@pytest.mark.crud
@pytest.mark.asyncio
async def test_find_user_by_uuid__not_found(global_sessionmaker):
    async with global_sessionmaker() as session:
        response = await find_user_by_uuid(db=session,
                                           user_uuid=uuid.uuid7())
    assert response is None


@pytest.mark.crud
@pytest.mark.asyncio
async def test_change_user_data(global_sessionmaker):
    async with global_sessionmaker() as session:
        user = test_users[0]
        new_data = test_users[1]
        response_create = await create_user(db=session, user_data=user)
        async with change_user_data(
            db=session,
            user_uuid=response_create.user_uuid
        ) as db_user:
            db_user[0].password = hash_password(new_data.password)
            db_user[0].email = new_data.email
        response_find = await find_user_by_email(db=session,
                                                 user_email=new_data.email)
        assert response_create.user_uuid == response_find.user_uuid
        assert response_create.email != response_find.email
        assert response_create.password != response_find.password


@pytest.mark.crud
@pytest.mark.asyncio
async def test_delete_user(global_sessionmaker):
    async with global_sessionmaker() as session:
        user = test_users[0]
        response_create = await create_user(db=session,
                                            user_data=user)
        response_delete = await delete_user(db=session,
                                            user_email=user.email)
        response_find = await find_user_by_email(db=session,
                                                 user_email=user.email)
        assert response_delete is True
        assert response_find is None
        assert isinstance(response_create, DbUserData)
        assert isinstance(response_create.user_uuid, uuid.UUID)
