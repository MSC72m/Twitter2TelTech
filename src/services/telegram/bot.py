import logging
from pyexpat.errors import messages
from telebot.types import Message
from telebot.async_telebot import AsyncTeleBot
from app.app import generate_app
from handlers.handler import handler_start_command, handler_sign_up
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create bot instance
bot : AsyncTeleBot = generate_app()

# Create handler for bot message
@bot.message_handler(commands=['start'])
async def start_command(message: Message):
    await handler_start_command(bot, message)

@bot.message_handler(func=lambda message: True if message.text == "sign up" else False)
async def sign_up(message: Message):
    await handler_sign_up(bot, message)

async def main():
    await bot.infinity_polling()

if __name__ == "__main__":
    logger.info("Bot started")
    asyncio.run(main())