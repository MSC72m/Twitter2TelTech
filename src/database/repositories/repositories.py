from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select, update, delete, insert
from src.database.repositories.base_repo import BaseRepository
from src.database.models.pydantic_models import Tweet 
from src.database.models.models import User, TwitterAccount, user_account_subscriptions, user_category_subscriptions, Tweet as TweetModel
from typing import Dict, Tuple, List, Optional, Any

class TweetRepository(BaseRepository[TweetModel]):
    async def get_by_id(self, _id: int):
        async with self.session() as session:
            result = await session.execute(select(TweetModel).filter(TweetModel._id== _id))
            return result.scalars().first()

    async def tweet_exists(self, tweet_id: str):
        async with self.session() as session:
            result = await session.execute(select(TweetModel._id).where(TweetModel.twitter_id == tweet_id))
            return result.scalars().first() is not None
    
    async def get_all_ids(self):
        async with self.session() as session:
            result = await session.execute(select(TweetModel._id))
            return result.scalars().all()


class TwitterAccountRepository(BaseRepository[TwitterAccount]):
    async def get_id_by_username(self, username: str):
        async with self.session() as session:
            result = await session.excute(select(TwitterAccount._id).where(TwitterAccount.username == username))
            return result.scalars().first() 

    async def get_category_id_by_account_id(self, account_id: int):
        async with self.session() as session:
            result = await session.execute(select(TwitterAccount.category_id).where(TwitterAccount._id == account_id))
            return result.scalars().first()

    async def get_twitter_accounts(self):
        async with self.session() as session:
            result = await session.execute(select(TwitterAccount.username))
            return result.scalars().all()

    async def get_all_account_ids_with_category(self) -> List[Tuple[str, int, int]]:
        async with self.session() as session:
            result = await session.execute(select(TwitterAccount._id, TwitterAccount.category_id))
            return result.scalars().all()



class UserRepository(BaseRepository[User]):
    async def get_all_subscribed_categories(self, user_id: int) -> List[Tuple[str, int]]:
        async with self.session() as session:
            result = await session.execute(user_category_subscriptions.select(user_category_subscriptions.c.account_id, user_category_subscriptions.c.category_id).where(user_category_subscriptions.c.user_id == user_id))
            return result.scalars().all()

    async def get_all_subscribed_accounts(self, user_id: int) -> List[int]:
        async with self.session() as session:
            result = await session.execute(user_account_subscriptions.select(user_account_subscriptions.c.account_id).where(user_account_subscriptions.c.user_id == user_id))
            return result.scalars().all()

