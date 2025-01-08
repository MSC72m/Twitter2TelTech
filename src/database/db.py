import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from src.core.config import DB_CONFIG 

logger = logging.getLogger(__name__)

DB_URL = DB_CONFIG.db_url
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
    from src.database.models.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())