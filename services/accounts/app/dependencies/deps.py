from typing import AsyncGenerator
from fastapi import (Depends,
                     HTTPException,
                     status)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import (HTTPBearer,
                              HTTPAuthorizationCredentials)

from app.db.database import async_session_factory
from app.core.security import decode_token
from app.schemas.pydantic_schemas import (AccessTokensPayload,
                                          RefreshTokensPayload)


auth_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as db:
        yield db


def verify_access_token(
        token: HTTPAuthorizationCredentials = Depends(auth_scheme)
        ) -> AccessTokensPayload:
    payload = decode_token(token=token.credentials)
    if payload.token_type != 'access':
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail=[{"loc": ["header", "Authorization"],
                      "msg": "need access token",
                      "type": "wrong-token"}],
             headers={"WWW-Authenticate": "Bearer"}
                      )
    return payload


def verify_refresh_token(
        token: HTTPAuthorizationCredentials = Depends(auth_scheme)
        ) -> RefreshTokensPayload:
    payload = decode_token(token=token.credentials)
    if payload.token_type != 'refresh':
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail=[{"loc": ["header", "Authorization"],
                      "msg": "need refresh token",
                      "type": "wrong-token"}],
             headers={"WWW-Authenticate": "Bearer"}
                                )
    return payload
