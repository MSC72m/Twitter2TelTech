from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.database.base import Base

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: T, session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[T]:
        result = await self.session.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_all(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.commit()
        return obj

    async def create_all(self, objs: List[T]) -> List[T]:
        self.session.add_all(objs)
        await self.session.commit()
        return objs

    async def update(self, obj: T) -> T:
        await self.session.merge(obj)
        await self.session.commit()
        return obj

    async def delete(self, obj: T) -> None:
        await self.session.execute(delete(self.model).where(self.model.id == obj.id))
        await self.session.commit()