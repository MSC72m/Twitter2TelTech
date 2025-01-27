from pydantic import BaseModel

class SubscribeUserAccount(BaseModel):
    telegram_id: int
    daily_digest: bool
    weekly_digest: bool

class GetTelegramUser(BaseModel):
    telegram_id: int