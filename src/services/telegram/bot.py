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
from src.services.telegram.ruls.rules import is_follow_account, is_follow_category

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

@bot.message_handler(func=is_follow_category)
async def follow_category(message: Message):
    await handler_follow_category(bot, message, rdb)

@bot.message_handler(func=is_follow_account)
async def follow_account(message: Message):
    await handler_follow_account(bot, message, rdb)

@bot.callback_query_handler(func=lambda call: True)
async def handler_callback_query(call: CallbackQuery):
    await handle_callback_query(bot, call, rdb)

async def main():
    try:
        await bot.infinity_polling()
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    logger.info("Bot started")
    asyncio.run(main())
