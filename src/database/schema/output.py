from datetime import datetime
from pydantic import BaseModel

class OutputTelegramUser(BaseModel):
    telegram_id: int
    created_at: datetime
    is_active: bool
    daily_digest: bool
    weekly_digest: bool
    last_digest_sent: datetime