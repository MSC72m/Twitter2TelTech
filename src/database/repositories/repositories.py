from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select, update, delete, insert
from src.database.repositories.base_repo import BaseRepository
from src.database.models.pydantic_models import Tweet 
from src.database.models.models import TwitterAccount, Tweet as TweetModel

class TweetRepository(BaseRepository[TweetModel]):
    async def get_by_id(self, id: int):
        async with self.session() as session:
            result = await session.execute(select(self.model).filter(self.model.id == id))
            return result.scalars().first()

    async def tweet_exists(self, tweet_id: str):
        async with self.session() as session:
            result = await session.execute(select(self.model).where(self.model.twitter_id == tweet_id))
            return result.scalars().first() is not None


class TwitterAccountRepository(BaseRepository[TwitterAccount]):
    async def get_by_username(self, username: str):
        async with self.session() as session:
            result = await session.excute(select(self.model).where(self.model.username == username))
            return result.scalars().first() 

    async def get_twitter_accounts(self):
        async with self.session() as session:
            result = await session.execute(select(self.model.username))
            return result.scalars().all()