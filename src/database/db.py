from dotenv import load_dotenv
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.database.base import Base

logger = logging.getLogger(__name__)
load_dotenv()

DB_URL = os.getenv("DB_URL")

# Use aiosqlite for async support
engine = create_async_engine(DB_URL, echo=True)

# Configure AsyncSession
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())