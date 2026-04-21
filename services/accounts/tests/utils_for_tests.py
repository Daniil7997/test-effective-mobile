from datetime import datetime, timezone
import uuid
from unittest.mock import MagicMock

import jwt

from app.core.security import PRIVATE_KEY, TOKEN_ALGORITHM
from app.logic.main_logic import get_time_for_jwt
from app.schemas.pydantic_schemas import (GetTokens,
                                          User,
                                          AccessTokensPayload,
                                          RefreshTokensPayload)


test_users = (
    User(email="user1@gmail.com", password="verycoolPass"),
    User(email="user2@gmail.com", password="strongpas"),
    User(email="user2@gmail.com", password="password123")
    )


class TestPassword:
    password = 'MyStrongPassword'
    hashed_password = ('$argon2id$v=19$m=65536,t=3,p=4$Rm81aqXN6zHvrSasfb3'
                       '46A$Vjzf0rczccXVvwiZJnuPxxp+L0uCA1c8Cs3s7sRA5KI')


def create_expired_tokens(user_uuid: uuid.UUID, role) -> GetTokens:
    now_unix = int(datetime.now(timezone.utc).timestamp())
    exp_access_unix = get_time_for_jwt(now=now_unix, minutes=-15)
    exp_refresh_unix = get_time_for_jwt(now=now_unix, days=-2)

    json_access_payload = AccessTokensPayload(
        sub=user_uuid,  # ID пользователя
        iat=now_unix,  # Время создания
        exp=exp_access_unix,  # Время действия
        role=role,  # роль
        token_type="access"  # Тип токена
    ).model_dump(mode='json')

    json_refresh_payload = RefreshTokensPayload(
        sub=user_uuid,
        iat=now_unix,
        exp=exp_refresh_unix,
        token_type="refresh"
    ).model_dump(mode='json')

    access_token = jwt.encode(json_access_payload,
                              PRIVATE_KEY,
                              algorithm=TOKEN_ALGORITHM)
    refresh_token = jwt.encode(json_refresh_payload,
                               PRIVATE_KEY,
                               algorithm=TOKEN_ALGORITHM)
    return GetTokens(access_token=access_token, refresh_token=refresh_token)


def create_mock_creds(token):
    mock = MagicMock()
    mock.credentials = token
    return mock
