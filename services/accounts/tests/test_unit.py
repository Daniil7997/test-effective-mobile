import uuid
from fastapi import HTTPException
import pytest
from datetime import datetime, timezone

from app.core.security import (verify_password,
                               hash_password,
                               create_tokens,
                               decode_token)
from app.logic.main_logic import get_time_for_jwt
from app.models.users import UserRole
from app.schemas.pydantic_schemas import (AccessTokensPayload,
                                          RefreshTokensPayload,
                                          GetTokens)
from app.dependencies.deps import (verify_access_token,
                                   verify_refresh_token)
from tests.utils_for_tests import (test_users,
                                   TestPassword,
                                   create_expired_tokens,
                                   create_mock_creds)


# ----------------- app/core/security.py --------------------
@pytest.mark.unit
def test_hash_password():
    user = test_users[0]
    hashed_pass = hash_password(user.password)
    assert user.password != hashed_pass


@pytest.mark.unit
def test_verify_password():
    true_verify = verify_password(raw_password=TestPassword.password,
                                  hash_password=TestPassword.hashed_password)
    assert true_verify is True


@pytest.mark.unit
def test_verify_password__wrong_password():
    false_verify = verify_password(
        raw_password=f'{TestPassword.password}wrongString',
        hash_password=TestPassword.hashed_password)
    assert false_verify is False


@pytest.mark.unit
def test_create_tokens_and_decode_token():
    test_uuid = uuid.uuid7()
    tokens = create_tokens(user_uuid=test_uuid,
                           role=UserRole.user)
    access_payload = decode_token(tokens.access_token)
    refresh_payload = decode_token(tokens.refresh_token)
    assert isinstance(tokens, GetTokens)
    assert isinstance(access_payload, AccessTokensPayload)
    assert isinstance(refresh_payload, RefreshTokensPayload)
    assert isinstance(access_payload.sub, uuid.UUID)
    assert isinstance(refresh_payload.sub, uuid.UUID)
    assert access_payload.token_type == 'access'
    assert refresh_payload.token_type == 'refresh'
    assert access_payload.role == UserRole.user
    assert access_payload.iat < access_payload.exp
    assert refresh_payload.iat < refresh_payload.exp
    assert len(str(access_payload.iat)) == 10
    assert len(str(refresh_payload.iat)) == 10
    assert len(str(access_payload.exp)) == 10
    assert len(str(refresh_payload.exp)) == 10


@pytest.mark.unit
def test_decode_token__expired():
    test_uuid = uuid.uuid7()
    tokens = create_expired_tokens(user_uuid=test_uuid,
                                   role=UserRole.user)
    with pytest.raises(HTTPException) as exc:
        decode_token(tokens.access_token)  # <-Exception
    assert exc.value.status_code == 401
    exc_dict = exc.value.detail[0]
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}
    assert isinstance(exc_dict["loc"], list)
    assert isinstance(exc_dict["msg"], str)
    assert isinstance(exc_dict["type"], str)
    assert "expire" in exc_dict["msg"].lower()
    assert "expire" in exc_dict["type"].lower()
    assert exc_dict["loc"] == ["header", "Authorization"]


@pytest.mark.unit
def test_decode_token__invalid():
    with pytest.raises(HTTPException) as exc:
        decode_token('wrong-token')  # <-Exception
    assert exc.value.status_code == 401
    exc_dict = exc.value.detail[0]
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}
    assert isinstance(exc_dict["loc"], list)
    assert isinstance(exc_dict["msg"], str)
    assert isinstance(exc_dict["type"], str)
    assert "invalid" in exc_dict["msg"].lower()
    assert "invalid" in exc_dict["type"].lower()
    assert exc_dict["loc"] == ["header", "Authorization"]
# ---------------------------------------------------------------


# -------------------- app/logic/main_logic.py ------------------
@pytest.mark.unit
def test_get_time_for_jwt():
    now_unix = int(datetime.now(timezone.utc).timestamp())
    time_5min = get_time_for_jwt(now=now_unix, minutes=5)
    time_5hours = get_time_for_jwt(now=now_unix, hours=5)
    multi_time = get_time_for_jwt(now=now_unix,
                                  minutes=2,
                                  hours=1,
                                  days=2)
    assert len(str(time_5min)) == 10
    assert len(str(time_5hours)) == 10
    assert len(str(multi_time)) == 10
    assert time_5min < time_5hours
    assert time_5hours < multi_time
# ----------------------------------------------------------------


# ----------------- app/dependencies/deps.py ---------------------
def test_verify_access_token():
    tokens = create_tokens(user_uuid=uuid.uuid7(),
                           role=UserRole.user)
    mock = create_mock_creds(token=tokens.access_token)
    access_payload = verify_access_token(token=mock)
    assert access_payload.token_type == 'access'


def test_verify_access_token__refresh_token():
    tokens = create_tokens(user_uuid=uuid.uuid7(),
                           role=UserRole.user)
    mock = create_mock_creds(token=tokens.refresh_token)
    with pytest.raises(HTTPException) as exc:
        verify_access_token(token=mock)
    assert exc.value.status_code == 401
    detail = exc.value.detail[0]
    assert detail['loc'] == ["header", "Authorization"]
    assert detail['msg'] == 'need access token'
    assert detail['type'] == 'wrong-token'
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


def test_verify_refresh_token():
    tokens = create_tokens(user_uuid=uuid.uuid7(),
                           role=UserRole.user)
    mock = create_mock_creds(token=tokens.refresh_token)
    access_payload = verify_refresh_token(token=mock)
    assert access_payload.token_type == 'refresh'


def test_verify_refresh_token__access_token():
    tokens = create_tokens(user_uuid=uuid.uuid7(),
                           role=UserRole.user)
    mock = create_mock_creds(token=tokens.access_token)
    with pytest.raises(HTTPException) as exc:
        verify_refresh_token(token=mock)
    assert exc.value.status_code == 401
    detail = exc.value.detail[0]
    assert detail['loc'] == ["header", "Authorization"]
    assert detail['msg'] == 'need refresh token'
    assert detail['type'] == 'wrong-token'
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}
# ----------------------------------------------------------------
