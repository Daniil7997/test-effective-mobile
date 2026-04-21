import uuid

from httpx import ASGITransport, AsyncClient
import pytest

from app.main import application
from app.models.users import UserRole
from app.schemas.pydantic_schemas import (User,
                                          DbUserData,
                                          GetTokens)
from app.repositories.crud import (find_user_by_email,
                                   create_user)
from app.core.security import create_tokens, decode_token
from tests.utils_for_tests import test_users


# ------------------------ регистрация --------------------------
@pytest.mark.integration
@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        user: User = test_users[0]
        response = await ac.post(
            "/accounts",
            json={
                "email": user.email,
                "password": user.password
            }
        )
        assert response.status_code == 201
        assert isinstance(uuid.UUID(response.json()['user_uuid']), uuid.UUID)
        assert response.json()["email"] == user.email


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register__already_exist(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[0]
            await create_user(db=session, user_data=user)
            response = await ac.post(
                "/accounts",
                json={
                    "email": user.email,
                    "password": user.password
                }
            )
            assert response.status_code == 409
            response_dict = response.json()["detail"][0]
            assert len(response_dict) == 3
            assert isinstance(response_dict["loc"], str)
            assert isinstance(response_dict["msg"], str)
            assert isinstance(response_dict["type"], str)
            assert response_dict["loc"] == "email"
            assert "email" in response_dict["msg"].lower()
            assert response_dict["type"] == "conflict"
# ------------------------------------------------------------------


# ------------------------ мягкое удаление -------------------------
@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_user(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[0]
            db_user = await create_user(db=session, user_data=user)
            tokens = create_tokens(user_uuid=db_user.user_uuid,
                                   role=UserRole.user)
            response = await ac.request(
                method="DELETE",
                url="/accounts",
                json={
                    "password": user.password
                },
                headers={"Authorization": f"Bearer {tokens.access_token}"}
            )
            user_after_del = await find_user_by_email(db=session,
                                                      user_email=user.email)
            assert response.status_code == 200
            assert user_after_del is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_user__not_found(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        user: User = test_users[0]
        tokens = create_tokens(user_uuid=uuid.uuid7(),
                               role=UserRole.user)
        response = await ac.request(
            method="DELETE",
            url="/accounts",
            json={
                "password": user.password
            },
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        assert response.status_code == 404

        response_dict = response.json()["detail"][0]
        assert len(response_dict) == 3
        assert response_dict["loc"] == ["header", "Authorization"]
        assert response_dict["msg"] == ("User with this token "
                                        "does not exists")
        assert response_dict["type"] == "user-dont-exist"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_user__passwords_dont_match(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[0]
            db_user = await create_user(db=session, user_data=user)
            tokens = create_tokens(user_uuid=db_user.user_uuid,
                                   role=UserRole.user)
            response = await ac.request(
                method="DELETE",
                url="/accounts",
                json={
                    "password": f'wrong{user.password}'
                },
                headers={"Authorization": f"Bearer {tokens.access_token}"}
            )
            assert response.status_code == 403
            response_dict = response.json()["detail"][0]
            assert len(response_dict) == 3
            assert response_dict["loc"] == ["body", "password"]
            assert response_dict["msg"] == "The passwords don't match"
            assert response_dict["type"] == "access-denied"
# ------------------------------------------------------------------


# ------------------------ получение токена ------------------------
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_token(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[1]
            await create_user(db=session, user_data=user)
            response = await ac.post(
                "/tokens",
                json={
                    "email": user.email,
                    "password": user.password
                }
            )
            assert response.status_code == 200
            access_json = response.json()["access_token"]
            refresh_json = response.json()["refresh_token"]
            assert isinstance(access_json, str)
            assert isinstance(refresh_json, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_token__user_not_found(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        user: User = test_users[1]
        response = await ac.post(
            "/tokens",
            json={
                "email": user.email,
                "password": user.password
            }
        )
        assert response.status_code == 401
        response_dict = response.json()["detail"][0]
        assert len(response_dict) == 3
        assert isinstance(response_dict["loc"], list)
        assert len(response_dict["loc"]) == 2
        assert isinstance(response_dict["msg"], str)
        assert isinstance(response_dict["type"], str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_token__check_password_failed(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[1]
            await create_user(db=session, user_data=user)
            response = await ac.post(
                "/tokens",
                json={
                    "email": user.email,
                    "password": f"wrong{user.password}"
                }
            )
        assert response.status_code == 401
        response_dict = response.json()["detail"][0]
        assert len(response_dict) == 3
        assert isinstance(response_dict["loc"], list)
        assert len(response_dict["loc"]) == 2
        assert isinstance(response_dict["msg"], str)
        assert isinstance(response_dict["type"], str)
# -------------------------------------------------------------------


# ----------- получение access токена по refresh токену  ------------
@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[1]
            db_user: DbUserData = await create_user(db=session, user_data=user)
            tokens: GetTokens = create_tokens(user_uuid=db_user.user_uuid,
                                              role=db_user.role)
            response = await ac.post(
                "/refresh",
                headers={"Authorization": f"Bearer {tokens.refresh_token}"}
            )
        assert response.status_code == 200
        access_token = response.json()["token"]
        access_payload = decode_token(token=access_token)
        assert access_payload.token_type == 'access'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh__wrong_token(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[1]
            db_user: DbUserData = await create_user(db=session, user_data=user)
            tokens: GetTokens = create_tokens(user_uuid=db_user.user_uuid,
                                              role=db_user.role)
            response = await ac.post(
                "/refresh",
                headers={"Authorization": f"Bearer {tokens.access_token}"}
            )
        assert response.status_code == 401
        response_dict = response.json()["detail"][0]
        assert len(response_dict) == 3
        assert isinstance(response_dict["loc"], list)
        assert len(response_dict["loc"]) == 2
        assert response_dict["msg"] == "need refresh token"
# -------------------------------------------------------------------


# --------------------------- смена пароля --------------------------
@pytest.mark.integration
@pytest.mark.asyncio
async def test_change_password(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[0]
            db_user_before = await create_user(db=session, user_data=user)
            tokens = create_tokens(db_user_before.user_uuid,
                                   role=db_user_before.role)
            response = await ac.patch(
                "/accounts",
                json={
                    "current_password": user.password,
                    "new_data": {"password": f"{user.password}new"}
                },
                headers={"Authorization": f"Bearer {tokens.access_token}"}
            )
            assert response.status_code == 200
            db_user_after: DbUserData = await find_user_by_email(
                db=session,
                user_email=user.email
                )
            assert db_user_after.password != db_user_before.password


@pytest.mark.integration
@pytest.mark.asyncio
async def test_change_password__user_not_found(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[0]
            await create_user(db=session, user_data=user)
            tokens = create_tokens(uuid.uuid7(),
                                   role=UserRole.user)
            response = await ac.patch(
                "/accounts",
                json={
                    "current_password": user.password,
                    "new_data": {"password": f"{user.password}new"}
                },
                headers={"Authorization": f"Bearer {tokens.access_token}"}
            )
            assert response.status_code == 404
            response_dict = response.json()["detail"][0]
            assert len(response_dict) == 3
            assert isinstance(response_dict["loc"], list)
            assert isinstance(response_dict["msg"], str)
            assert isinstance(response_dict["type"], str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_change_password__password_dont_match(global_sessionmaker):
    async with AsyncClient(transport=ASGITransport(app=application),
                           base_url="http://test")as ac:
        async with global_sessionmaker() as session:
            user: User = test_users[0]
            db_user = await create_user(db=session, user_data=user)
            tokens = create_tokens(db_user.user_uuid,
                                   role=db_user.role)
            response = await ac.patch(
                "/accounts",
                json={
                    "current_password": f"wrong{user.password}",
                    "new_data": {"password": f"{user.password}new"}
                },
                headers={"Authorization": f"Bearer {tokens.access_token}"}
            )
            assert response.status_code == 403
            response_dict = response.json()["detail"][0]
            assert len(response_dict) == 3
            assert isinstance(response_dict["loc"], list)
            assert isinstance(response_dict["msg"], str)
            assert isinstance(response_dict["type"], str)
# -------------------------------------------------------------------
