import os
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot

def generate_app() -> AsyncTeleBot :
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in the environment variables.")

    bot = AsyncTeleBot(BOT_TOKEN)
    return bot
