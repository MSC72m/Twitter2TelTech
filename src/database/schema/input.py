from pydantic import BaseModel

class SubscribeAccount(BaseModel):
    telegram_id: int
    daily_digest: bool
    weekly_digest: bool
    twitter_account: str

class SubscribeCategory(BaseModel):
    telegram_id: int
    daily_digest: bool
    weekly_digest: bool
    twitter_category: int

class GetTelegramUser(BaseModel):
    telegram_id: int