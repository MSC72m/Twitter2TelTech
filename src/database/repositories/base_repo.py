from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.database.base import Base
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: T, session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[T]:
        try:
            logger.info(f"Fetching {self.model.__name__} by ID: {id}")
            result = await self.session.execute(select(self.model).filter(self.model.id == id))
            entity = result.scalars().first()
            if entity:
                logger.info(f"Found {self.model.__name__}: {entity}")
            else:
                logger.warning(f"No {self.model.__name__} found with ID: {id}")
            return entity
        except Exception as e:
            logger.error(f"Error in get: {e}")
            raise

    async def get_all(self) -> List[T]:
        try:
            logger.info(f"Fetching all {self.model.__name__} entities")
            result = await self.session.execute(select(self.model))
            entities = result.scalars().all()
            logger.info(f"Fetched {len(entities)} {self.model.__name__} entities")
            return entities
        except Exception as e:
            logger.error(f"Error in get_all: {e}")
            raise

    async def create(self, obj: T) -> T:
        try:
            logger.info(f"Creating {self.model.__name__}: {obj}")
            self.session.add(obj)
            await self.session.commit()
            logger.info(f"Created {self.model.__name__}: {obj}")
            return obj
        except Exception as e:
            logger.error(f"Error in create: {e}")
            raise

    async def create_all(self, objs: List[T]) -> List[T]:
        try:
            logger.info(f"Creating multiple {self.model.__name__} entities")
            self.session.add_all(objs)
            await self.session.commit()
            logger.info(f"Created {len(objs)} {self.model.__name__} entities")
            return objs
        except Exception as e:
            logger.error(f"Error in create_all: {e}")
            raise

    async def update(self, obj: T) -> T:
        try:
            logger.info(f"Updating {self.model.__name__}: {obj}")
            await self.session.merge(obj)
            await self.session.commit()
            logger.info(f"Updated {self.model.__name__}: {obj}")
            return obj
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise

    async def delete(self, obj: T) -> None:
        try:
            logger.info(f"Deleting {self.model.__name__}: {obj}")
            await self.session.execute(delete(self.model).where(self.model.id == obj.id))
            await self.session.commit()
            logger.info(f"Deleted {self.model.__name__}: {obj}")
        except Exception as e:
            logger.error(f"Error in delete: {e}")
            raise
        