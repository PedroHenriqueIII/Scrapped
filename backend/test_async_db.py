import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async def test():
    DATABASE_URL = "postgresql+asyncpg://pedroribh:teste123@localhost:5432/scrapped"
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT 1"))
        print("Connected!")
        print(result.fetchall())

asyncio.run(test())
