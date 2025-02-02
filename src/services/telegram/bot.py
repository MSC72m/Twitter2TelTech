import logging
from telebot.types import Message
from telebot.async_telebot import AsyncTeleBot
from app.app import generate_app
from handlers.handler import handler_start_command, handler_follow_category, handler_follow_account
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
from src.cache.cache import get_cache_session
from src.cache.payload import RedisPayload

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure redis
rdb = get_cache_session()

# Create bot instance
bot : AsyncTeleBot = generate_app()

# Create handler for bot message
@bot.message_handler(commands=['start'])
async def start_command(message: Message):
    await handler_start_command(bot, message)

@bot.message_handler(func=lambda message: True if message.text == "Follow Category" else False)
async def follow_category(message: Message):
    payload = RedisPayload(
            twitter_account = False,
            twitter_category = True,
            account = "",
            category = 0,
            )
    status = rdb.set(message.from_user.id, payload.model_dump_json())
    logger.info(f"{status} {message.from_user.id} set {payload}")
    await handler_follow_category(bot, message)

@bot.message_handler(func=lambda message: True if message.text == "Follow Account" else False)
async def follow_account(message: Message):
    payload = RedisPayload(
            twitter_account = True,
            twitter_category = False,
    account = "",
            category = 0,
            )
    status = rdb.set(message.from_user.id, payload.model_dump_json())
    logger.info(f"{status} {message.from_user.id} set {payload}")
    await handler_follow_account(bot, message)

async def main():
    await bot.infinity_polling()

if __name__ == "__main__":
    logger.info("Bot started")
    asyncio.run(main())
