from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select, update, delete, insert
from src.database.base import Base

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Optional[T]:
        async with self.session() as session:
            result = await session.execute(select(self.model).filter(self.model._id == id))
            return result.scalars().first()

    async def get_all(self) -> List[T]:
        async with self.session() as session:
            result = await session.execute(select(self.model))
            return result.scalars().all()

    async def create(self, obj: T) -> T:
        async with self.session() as session:
            session.add(obj)
            await session.commit()
            return obj

    async def update(self, obj: T) -> T:
        async with self.session() as session:
            await session.execute(update(self.model).where(self.model._id == obj._id).values(obj))
            await session.commit()
            return obj

    async def delete(self, obj: T) -> None:
        async with self.session() as session:
            await session.execute(delete(self.model).where(self.model._id == obj._id))
            await session.commit()