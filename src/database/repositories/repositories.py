import uuid
from datetime import datetime, timezone

from sqlalchemy.engine import row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, Integer
from typing import Dict, Tuple, List, Optional, Any, Sequence
import logging
from uuid import UUID

from src.database.repositories.base_repo import BaseRepository
from src.database.models.pydantic_models import TweetDB, Category
from src.database.models.models import User, TwitterAccount, twitter_account_categories, user_account_subscriptions, user_category_subscriptions, Category as Categories ,Tweet as TweetModel
from src.database.schema.input import SubscribeUserAccount, GetTelegramUser
from src.database.schema.output import OutputTelegramUser

logger = logging.getLogger(__name__)

class TweetRepository(BaseRepository[TweetModel]):
    async def get_by_id(self, _id: int):
        try:
            logger.debug(f"Fetching tweet by ID: {_id}")
            result = await self.session.execute(select(TweetModel).filter(TweetModel.id == _id))
            tweet = result.scalars().first()
            if tweet:
                logger.debug(f"Found tweet: {tweet}")
            else:
                logger.warning(f"No tweet found with ID: {_id}")
            return tweet
        except Exception as e:
            logger.error(f"Error in get_by_id: {e}")
            raise

    async def tweet_exists(self, tweet_id: str):
        try:
            logger.debug(f"Checking if tweet exists with ID: {tweet_id}")
            result = await self.session.execute(select(TweetModel.id).where(TweetModel.twitter_id == tweet_id))
            exists = result.scalars().first() is not None
            logger.debug(f"Tweet exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error in tweet_exists: {e}")
            raise

    async def get_all_ids(self):
        try:
            logger.debug("Fetching all tweet IDs")
            result = await self.session.execute(select(TweetModel.twitter_id))
            ids = result.scalars().all()
            logger.debug(f"Fetched {len(ids)} tweet IDs")
            return ids
        except Exception as e:
            logger.error(f"Error in get_all_ids: {e}")
            raise

class TwitterAccountRepository(BaseRepository[TwitterAccount]):
    async def get_account_details(self):
        try:
            logger.debug("Fetching all Twitter account details")
            result = await self.session.execute(select(TwitterAccount.id, TwitterAccount.username))
            accounts = result.fetchall()
            logger.debug(f"Fetched {len(accounts)} account details")
            return [account for account in accounts]
        except Exception as e:
            logger.error(f"Error in get_account_details: {e}")
            raise

    async def get_id_by_username(self, username: str):
        try:
            logger.debug(f"Fetching account ID for username: {username}")
            result = await self.session.execute(select(TwitterAccount.id).where(TwitterAccount.username == username))
            account_id = result.scalars().first()
            if account_id:
                logger.debug(f"Found account ID: {account_id}")
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
            logger.debug("Fetching all Twitter accounts")
            result = await self.session.execute(select(TwitterAccount.username))
            accounts = result.scalars().all()
            logger.debug(f"Fetched {len(accounts)} accounts")
            return accounts
        except Exception as e:
            logger.error(f"Error in get_twitter_accounts: {e}")
            raise

    async def update_last_fetched(self, screen_user_name: str):
        try:
            logger.debug("Updating last fetched")
            # Correct usage of update
            stmt = (
                update(TwitterAccount)
                .where(TwitterAccount.username == screen_user_name)
                .values(last_fetched=datetime.now(timezone.utc))
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error in update_last_fetched: {e}")
            await self.session.rollback()
            raise

class CategoryRepository(BaseRepository[Category]):
    async def get_account_category_mappings(self) -> List[Tuple[int, int]]:
        try:
            # Correct select syntax for SQLAlchemy
            query = select(
                twitter_account_categories.c.twitter_account_id,
                twitter_account_categories.c.category_id
            )
            result = await self.session.execute(query)
            rows = result.fetchall()
            # Ensure we're working with integers
            return [(int(row[0]), int(row[1])) for row in rows]
        except Exception as e:
            logger.error(f"Error in get_account_category_mappings: {e}")
            raise

    async def get_all_category_info(self):
        try:
            query = select(
                Categories
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error in get_all_categories: {e}")
            raise

    async def get_category_by_id(self, category_id: int):
        try:
            query = select(
                Categories
            ).where(
                Categories.id == category_id
            )
            result = await self.session.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Error in get_all_categories: {e}")
            raise

class UserRepository(BaseRepository[User]):
    async def get_all_subscribed_categories(self, user_id: UUID) -> List[int]:
        try:
            logger.debug(f"Fetching all subscribed categories for user ID: {user_id}")
            result = await self.session.execute(
                select(user_category_subscriptions.c.category_id)
                .where(user_category_subscriptions.c.user_id == user_id)
            )
            categories = result.scalars().all()
            logger.debug(f"Fetched {len(categories)} subscribed categories")
            return categories
        except Exception as e:
            logger.error(f"Error in get_all_subscribed_categories: {e}")
            raise

    async def get_all_subscribed_accounts(self, user_id: UUID) -> List[int]:
        try:
            logger.debug(f"Fetching all subscribed accounts for user ID: {user_id}")
            result = await self.session.execute(
                select(user_account_subscriptions.c.account_id)
                .where(user_account_subscriptions.c.user_id == user_id)
            )
            accounts = result.scalars().all()
            logger.debug(f"Fetched {len(accounts)} subscribed accounts")
            return accounts
        except Exception as e:
            logger.error(f"Error in get_all_subscribed_accounts: {e}")
            raise

    async def get_telegram_user(self, user_input: GetTelegramUser) -> OutputTelegramUser:
        try:
            logger.debug(f"Fetching telegram user for user ID: {user_input.telegram_id}")
            result = await self.session.execute(
                select(User)
                .where(User.telegram_id == user_input.telegram_id)
            )
            user = result.scalars().first()
            logger.debug(f"Fetched {user.telegram_id} telegram user accounts")
            return OutputTelegramUser(
                telegram_id=user.telegram_id,
                created_at=user.created_at,
                is_active=user.is_active,
                daily_digest=user.daily_digest,
                weekly_digest=user.weekly_digest,
                last_digest_sent=user.last_digest_sent,
            )
        except Exception as e:
            logger.error(f"Error in get_all_subscribed_accounts: {e}")
            raise

    async def subscribe_user_account(self, user_input: SubscribeUserAccount) -> None:
        user = User(
            id = uuid.uuid4(),
            telegram_id = user_input.telegram_id,
            created_at=datetime.now(),
            is_active=True,
            daily_digest=user_input.daily_digest,
            weekly_digest=user_input.weekly_digest,
            last_digest_sent=None,
        )

        try:
            logger.debug(f"Create subscribed accounts for user ID: {user_input.telegram_id}")
            self.session.add(user)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error in subscribe_user_account: {e}")
            raise