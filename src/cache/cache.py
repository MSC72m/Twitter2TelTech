import logging
import os
from sys import exception
import redis
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_cache_session() -> redis.Redis:
    load_dotenv()
    host = os.getenv("REDIS_HOST")
    port = int(os.getenv("REDIS_PORT"))
    
    try:
        rds = redis.Redis(host=host, port=port, db=0)
        rds.ping()
        logger.debug("REDIS session created successfully")
        return rds
    except Exception as e:
        logger.error(f"Failed to create Redis session: {e}")
        raise
