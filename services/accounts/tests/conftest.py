import pytest

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.db.database import async_engine
from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def critical_check():
    if not settings.IS_TEST_DB:
        pytest.exit(f"Остановка всех тестов: БАЗА ДАННЫХ {settings.DB_NAME}"
                    f"НЕ ДЛЯ ТЕСТИРОВАНИЯ.")


@pytest.fixture(scope='function', autouse=True)
async def db_truncate(critical_check):
    async with async_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE auth_users;"))
    yield


@pytest.fixture(scope='session')
async def global_engine() -> AsyncEngine:
    return async_engine


@pytest.fixture(scope='session')
async def global_sessionmaker(global_engine):
    async_session_factory: async_sessionmaker = async_sessionmaker(
        bind=global_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False
    )
    return async_session_factory
