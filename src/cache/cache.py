import logging
import os
from sys import exception
import redis
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_cache_session() -> redis.Redis:
    load_dotenv()
    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", "6379"))
    global _redis_instance
    if _redis_instance is not None:
        return _redis_instance

    try:
        _redis_instance = redis.Redis(host=host, port=port, db=0)
        _redis_instance.ping()
        logger.debug("REDIS session created successfully")
        return _redis_instance
    except Exception as e:
        logger.error(f"Failed to create Redis session: {e}")
        raise
