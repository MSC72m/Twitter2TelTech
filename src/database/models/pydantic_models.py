from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional
import datetime

class TwitterCredentials(BaseModel):
    """Pydantic model to store Twitter credentials"""
    username: str
    password: str
    email: str


class Tweet(BaseModel):
    """Pydantic model to store tweet information"""
    _id: int 
    twitter_id: str
    account_id: int
    category_id: int
    content: str
    media_urls: Optional[List[str]] = None
    created_at: datetime.datetime


class Category(BaseModel):
    """Pydantic model to store category information"""
    _id: int
    name: str
    description: str
    is_active: bool


class TwitterAccount(BaseModel):
    """Pydantic model to store Twitter account information"""
    _id: int
    username: str
    display_name: str
    last_fetched: Optional[datetime.datetime] = None
    is_active: bool

class InitialTweetState(BaseModel):
    """Pydantic model to store initial tweet state"""
    tweets: List[Dict]



class CrawlAccountDetails(BaseModel):
    """Pydantic model to store account details"""
    username: str
    days_to_crawl: int
    tweet_count: int


class TweetDetails(BaseModel):
    """Pydantic model to store tweet details"""
    _id: int
    date: datetime.datetime