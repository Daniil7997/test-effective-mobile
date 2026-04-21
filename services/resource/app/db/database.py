from sqlalchemy.ext.asyncio import (create_async_engine, 
                                    AsyncEngine, 
                                    async_sessionmaker)

from app.core.config import settings


async_engine: AsyncEngine = create_async_engine(
    url=settings.url_db_asyncpg,
    echo=True,
    )


async_session_factory: async_sessionmaker = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)
