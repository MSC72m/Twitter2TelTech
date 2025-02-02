import os
from dotenv import load_dotenv
import logging
from telebot.async_telebot import AsyncTeleBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_app() -> AsyncTeleBot :
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set on the environment variables.")
        raise ValueError("BOT_TOKEN is not set in the environment variables.")

    bot = AsyncTeleBot(BOT_TOKEN)

    logger.info("Bot instance created successfully.")
    return bot
