from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.repositories.base_repo import BaseRepository
from src.database.models.pydantic_models import Tweet 
from src.database.models.models import User, TwitterAccount, user_account_subscriptions, user_category_subscriptions, Tweet as TweetModel
from typing import Dict, Tuple, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TweetRepository(BaseRepository[TweetModel]):
    async def get_by_id(self, _id: int):
        try:
            logger.info(f"Fetching tweet by ID: {_id}")
            result = await self.session.execute(select(TweetModel).filter(TweetModel.id == _id))
            tweet = result.scalars().first()
            if tweet:
                logger.info(f"Found tweet: {tweet}")
            else:
                logger.warning(f"No tweet found with ID: {_id}")
            return tweet
        except Exception as e:
            logger.error(f"Error in get_by_id: {e}")
            raise

    async def tweet_exists(self, tweet_id: str):
        try:
            logger.info(f"Checking if tweet exists with ID: {tweet_id}")
            result = await self.session.execute(select(TweetModel.id).where(TweetModel.twitter_id == tweet_id))
            exists = result.scalars().first() is not None
            logger.info(f"Tweet exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error in tweet_exists: {e}")
            raise

    async def get_all_ids(self):
        try:
            logger.info("Fetching all tweet IDs")
            result = await self.session.execute(select(TweetModel.twitter_id))
            ids = result.scalars().all()
            logger.info(f"Fetched {len(ids)} tweet IDs")
            return ids
        except Exception as e:
            logger.error(f"Error in get_all_ids: {e}")
            raise


class TwitterAccountRepository(BaseRepository[TwitterAccount]):
    async def get_id_by_username(self, username: str):
        try:
            logger.info(f"Fetching account ID for username: {username}")
            result = await self.session.execute(select(TwitterAccount.id).where(TwitterAccount.username == username))
            account_id = result.scalars().first()
            if account_id:
                logger.info(f"Found account ID: {account_id}")
            else:
                logger.warning(f"No account found for username: {username}")
            return account_id
        except Exception as e:
            logger.error(f"Error in get_id_by_username: {e}")
            raise

    async def get_category_id_by_account_id(self, account_id: int):
        try:
            logger.info(f"Fetching category ID for account ID: {account_id}")
            result = await self.session.execute(select(TwitterAccount.category_id).where(TwitterAccount.id == account_id))
            category_id = result.scalars().first()
            if category_id:
                logger.info(f"Found category ID: {category_id}")
            else:
                logger.warning(f"No category found for account ID: {account_id}")
            return category_id
        except Exception as e:
            logger.error(f"Error in get_category_id_by_account_id: {e}")
            raise

    async def get_twitter_accounts(self):
        try:
            logger.info("Fetching all Twitter accounts")
            result = await self.session.execute(select(TwitterAccount.username))
            accounts = result.scalars().all()
            logger.info(f"Fetched {len(accounts)} accounts")
            return accounts
        except Exception as e:
            logger.error(f"Error in get_twitter_accounts: {e}")
            raise

    async def get_all_account_ids_with_category(self) -> List[Tuple[int, str, int]]:
        try:
            logger.info("Fetching all account IDs with categories")
            result = await self.session.execute(select(TwitterAccount.id, TwitterAccount.username, TwitterAccount.category_id))
            accounts = result.all()
            logger.info(f"Fetched {len(accounts)} accounts with categories")
            return accounts
        except Exception as e:
            logger.error(f"Error in get_all_account_ids_with_category: {e}")
            raise


class UserRepository(BaseRepository[User]):
    async def get_all_subscribed_categories(self, user_id: int) -> List[Tuple[str, int]]:
        try:
            logger.info(f"Fetching all subscribed categories for user ID: {user_id}")
            result = await self.session.execute(
                select(user_category_subscriptions.c.account_id, user_category_subscriptions.c.category_id)
                .where(user_category_subscriptions.c.user_id == user_id)
            )
            categories = result.all()
            logger.info(f"Fetched {len(categories)} subscribed categories")
            return categories
        except Exception as e:
            logger.error(f"Error in get_all_subscribed_categories: {e}")
            raise

    async def get_all_subscribed_accounts(self, user_id: int) -> List[int]:
        try:
            logger.info(f"Fetching all subscribed accounts for user ID: {user_id}")
            result = await self.session.execute(
                select(user_account_subscriptions.c.account_id)
                .where(user_account_subscriptions.c.user_id == user_id)
            )
            accounts = result.scalars().all()
            logger.info(f"Fetched {len(accounts)} subscribed accounts")
            return accounts
        except Exception as e:
            logger.error(f"Error in get_all_subscribed_accounts: {e}")
            raise

        