import asyncio
from app.core.database import AsyncSessionLocal

async def test():
    try:
        async with AsyncSessionLocal() as session:
            print("Connected!")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
