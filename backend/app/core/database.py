from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.settings import get_settings

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

engine = async_engine


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db_sync():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async_session = AsyncSessionLocal()
    try:
        session = loop.run_until_complete(async_session.__aenter__())
        yield session
    finally:
        loop.run_until_complete(async_session.__aexit__(None, None, None))
        loop.close()