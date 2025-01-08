from dotenv import load_dotenv
import os
from src.database.models.pydantic_models import DBConfig, TwitterCredentials 


load_dotenv()

TWITTER_CREDENTIALS = TwitterCredentials(
    username=os.getenv("TWITTER_USERNAME"),
    email=os.getenv("TWITTER_EMAIL"),
    password=os.getenv("TWITTER_PASSWORD")
)

DB_CONFIG = DBConfig(
    db_url=os.getenv("DB_URL", "sqlite+aiosqlite:///./db.sqlite3")
)
