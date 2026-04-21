from typing import AsyncGenerator
from fastapi import (Depends,
                     HTTPException,
                     status)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import (HTTPBearer,
                              HTTPAuthorizationCredentials)
from redis.asyncio import Redis

from app.db.database import async_session_factory
from app.core.security import decode_token
from app.schemas.pydantic_schemas import AccessTokensPayload
from app.core.config import settings
from app.models.base import UserRole


auth_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as db:
        yield db


def verify_access_token(
        token: HTTPAuthorizationCredentials = Depends(auth_scheme)
        ) -> AccessTokensPayload:
    payload: AccessTokensPayload = decode_token(token=token.credentials)
    if payload.token_type != 'access':
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail=[{"loc": ["header", "Authorization"],
                      "msg": "need access token",
                      "type": "wrong-token"}],
             headers={"WWW-Authenticate": "Bearer"}
                      )
    return payload


# пример как работать с Redis без декораторов.
async def get_redis():
    client = Redis.from_url(settings.url_redis, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def check_admin(payload: AccessTokensPayload = Depends(verify_access_token)):
    if payload.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[{"loc": ["header", "Authorization"],
                     "msg": "only for admins",
                     "type": "access-denied"}],
        )
