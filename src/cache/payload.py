from pydantic import BaseModel


class RedisPayload(BaseModel):
    twitter_account: bool
    twitter_category: bool
    account: str
    category: int
