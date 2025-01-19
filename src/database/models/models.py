from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, UUID, ForeignKey, Text, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from uuid import uuid4
from src.database.base import Base

# research on normolization costs and where it should be used.
# store procedure
# ask about what sql db's lack compared to nosql's and where to choose each.
# can you put it into a a excel spreed sheet or not if yes put it into sql
# what is the query type you do?
# is it more tailered towards querying about connection between documents or the content meaning it self.
# column family dbs

# Many to Many 3d Table
user_category_subscriptions = Table(
    'user_category_subscriptions',
    Base.metadata,
    Column('user_id', UUID, ForeignKey('users.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

user_account_subscriptions = Table(
    'user_account_subscriptions',
    Base.metadata,
    Column('user_id', UUID, ForeignKey('users.id')),
    Column('account_id', Integer, ForeignKey('twitter_accounts.id'))
)

twitter_account_categories = Table(
    'twitter_account_categories',
    Base.metadata,
    Column('twitter_account_id', Integer, ForeignKey('twitter_accounts.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True, default=uuid4)
    telegram_id = Column(Integer, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Subscription preferences
    daily_digest = Column(Boolean, default=False)
    weekly_digest = Column(Boolean, default=False)
    last_digest_sent = Column(DateTime)

    # Relationships
    subscribed_categories = relationship("Category", secondary=user_category_subscriptions)
    subscribed_accounts = relationship("TwitterAccount", secondary=user_account_subscriptions)
    delivered_tweets = relationship("DeliveredTweet")


class TwitterAccount(Base):
    __tablename__ = 'twitter_accounts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    last_fetched = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    tweets = relationship("Tweet", back_populates="account")
    categories = relationship("Category", secondary=twitter_account_categories)


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relationships
    tweets = relationship("Tweet", back_populates="category")


class Tweet(Base):
    __tablename__ = 'tweets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    twitter_id = Column(String, unique=True, nullable=False)
    text = Column(Text)
    created_at = Column(DateTime, nullable=False)
    media_urls = Column(JSON)  # Store as JSON array

    # Foreign Keys
    account_id = Column(Integer, ForeignKey('twitter_accounts.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))

    # Relationships
    account = relationship("TwitterAccount", back_populates="tweets")
    category = relationship("Category", back_populates="tweets")
    delivered_to = relationship("DeliveredTweet")


class DeliveredTweet(Base):
    __tablename__ = 'delivered_tweets'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id'))
    tweet_id = Column(Integer, ForeignKey('tweets.id'))
    delivered_at = Column(DateTime, default=datetime.utcnow)