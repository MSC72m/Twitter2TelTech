import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from src.database.db import get_session
from src.database.models.models import Category, TwitterAccount
from src.database.repositories.repositories import CategoryRepository, TwitterAccountRepository
from src.services.telegram.keyboards.keyboard import category_list_button, account_list_button
from src.cache.cache import get_cache_session



async def handler_start_command(bot: AsyncTeleBot, message: Message) -> None:
    markup = types.ReplyKeyboardMarkup(row_width=1)
    account_button = types.KeyboardButton('Follow Account')
    category_button = types.KeyboardButton('Follow Category')
    markup.add(account_button, category_button)
    await bot.send_message(message.from_user.id, "Choose one letter:", reply_markup=markup)


async def handler_follow_category(bot: AsyncTeleBot, message: Message) -> None:
    async with get_session() as session:
        category_repo = CategoryRepository(Category, session)
        category_list = await category_repo.get_all_category_info()
        markup = category_list_button(category_list)
    await bot.send_message(message.from_user.id, "Choose category" ,reply_markup=markup)

async def handler_follow_account(bot: AsyncTeleBot, message: Message) -> None:
    async with get_session() as session:
        account_repo = TwitterAccountRepository(TwitterAccount, session)
        account_list = await account_repo.get_twitter_accounts()
        markup = account_list_button(account_list)
    await bot.send_message(message.from_user.id, "Choose account", reply_markup=markup)

async def handler_text_command(bot: AsyncTeleBot, message: Message) -> None:
    await bot.reply_to(message, "Wrong Command")


async def handler_help_command(bot: AsyncTeleBot, message: Message) -> None:
    await bot.reply_to(message, "Help list command")


async def handle_callback_query(bot, call):
    pass
