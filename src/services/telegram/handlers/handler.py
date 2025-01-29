import os
import sys

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from src.database.db import get_session
from src.database.models.models import Category
from src.database.repositories.repositories import CategoryRepository
from src.services.telegram.keyboards.keyboard import category_list_button
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")



async def handler_start_command(bot: AsyncTeleBot, message: Message) -> None:
    markup = types.ReplyKeyboardMarkup(row_width=1)
    item_button = types.KeyboardButton('sign up')
    markup.add(item_button)
    await bot.send_message(message.from_user.id, "Choose one letter:", reply_markup=markup)


async def handler_sign_up(bot: AsyncTeleBot, message: Message) -> None:
    async with get_session() as session:
        category_repo = CategoryRepository(Category, session)
        category_list = await category_repo.get_all_category_info()
        markup = category_list_button(category_list)
    await bot.send_message(message.from_user.id,"Choose category" ,reply_markup=markup)


async def handler_text_command(bot: AsyncTeleBot, message: Message) -> None:
    await bot.reply_to(message, "Wrong Command")


async def handler_help_command(bot: AsyncTeleBot, message: Message) -> None:
    await bot.reply_to(message, "Help list command")


async def handle_callback_query(bot, call):
    if call.data == "option1":
        bot.answer_callback_query(call.id, "You chose Option 1!")
    elif call.data == "option2":
        bot.answer_callback_query(call.id, "You chose Option 2!")
