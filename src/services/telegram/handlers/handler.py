import logging
import os
import sys

import redis

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery

from src.database.db import get_session
from src.cache.payload import RedisPayload
from src.database.models.models import Category, TwitterAccount, User
from src.database.repositories.repositories import CategoryRepository, TwitterAccountRepository, UserRepository
from src.services.telegram.keyboards.keyboard import category_list_button, account_list_button, time_button
from src.database.schema.input import SubscribeAccount, SubscribeCategory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def handler_start_command(bot: AsyncTeleBot, message: Message) -> None:
    markup = types.ReplyKeyboardMarkup(row_width=1)
    account_button = types.KeyboardButton('Follow Account')
    category_button = types.KeyboardButton('Follow Category')
    markup.add(account_button, category_button)
    await bot.send_message(message.from_user.id, "Choose one letter:", reply_markup=markup)

async def handler_follow_category(bot: AsyncTeleBot, message: Message, rdb: redis.Redis) -> None:
    payload = RedisPayload(
        twitter_account=False,
        twitter_category=True,
        account="",
        category=0,
    )
    status = rdb.set(message.from_user.id, payload.model_dump_json())
    logger.info(f"{status} User {message.from_user.username} (ID: {message.from_user.id}) set {payload}")

    async with get_session() as session:
        category_repo = CategoryRepository(Category, session)
        category_list = await category_repo.get_all_category_info()
        markup = category_list_button(category_list)
    await bot.send_message(message.from_user.id, "Choose category" ,reply_markup=markup)

async def handler_follow_account(bot: AsyncTeleBot, message: Message, rdb: redis.Redis) -> None:
    payload = RedisPayload(
        twitter_account=True,
        twitter_category=False,
        account="",
        category=0,
    )
    status = rdb.set(message.from_user.id, payload.model_dump_json())
    logger.info(f"{status} User {message.from_user.username} (ID: {message.from_user.id}) set {payload}")

    async with get_session() as session:
        account_repo = TwitterAccountRepository(TwitterAccount, session)
        account_list = await account_repo.get_twitter_accounts()
        markup = account_list_button(account_list)
    await bot.send_message(message.from_user.id, "Choose account", reply_markup=markup)

async def handler_text_command(bot: AsyncTeleBot, message: Message) -> None:
    await bot.reply_to(message, "Wrong Command")

async def handler_help_command(bot: AsyncTeleBot, message: Message) -> None:
    await bot.reply_to(message, "Help list command")

async def handle_callback_query(bot: AsyncTeleBot, call: CallbackQuery, rdb: redis.Redis) -> None:
    key = rdb.getdel(str(call.from_user.id))
    if key:
        payload = RedisPayload.model_validate_json(key)
        if payload.twitter_account:
            payload.account = call.data
            status = rdb.set(call.from_user.id, payload.model_dump_json())
            logger.info(f"{status} User {call.from_user.username} (ID: {call.from_user.id}) set {payload}")
            markup = time_button()
            await bot.send_message(call.from_user.id, "choose time", reply_markup=markup)

        elif payload.twitter_category:
            payload.category = call.data
            status = rdb.set(call.from_user.id, payload.model_dump_json())
            logger.info(f"{status} User {call.from_user.username} (ID: {call.from_user.id}) set {payload}")
            markup = time_button()
            await bot.send_message(call.from_user.id, "choose time", reply_markup=markup)
    elif call.data == "daily" and key:
        payload = RedisPayload.model_validate_json(key)
        async with get_session as session:
            repo = UserRepository(User, session)
            if payload.twitter_account:
                user_input = SubscribeAccount(
                    telegram_id=call.from_user.id,
                    daily_digest=True,
                    weekly_digest=False,
                    twitter_account=payload.account
                )
                await repo.subscribe_user_account(user_input)
                await bot.send_message(call.from_user.id, "OK")
            elif payload.twitter_category:
                user_input = SubscribeCategory(
                    telegram_id=call.from_user.id,
                    daily_digest=True,
                    weekly_digest=False,
                    twitter_category=payload.category
                )
                await repo.subscribe_user_category(user_input)
                await bot.send_message(call.from_user.id, "OK")
    elif call.data == "weekly" and key:
        payload = RedisPayload.model_validate_json(key)
        async with get_session as session:
            repo = UserRepository(User, session)
            if payload.twitter_account:
                user_input = SubscribeAccount(
                    telegram_id=call.from_user.id,
                    daily_digest=False,
                    weekly_digest=True,
                    twitter_account=payload.account
                )
                await repo.subscribe_user_account(user_input)
                await bot.send_message(call.from_user.id, "OK")
            elif payload.twitter_category:
                user_input = SubscribeCategory(
                    telegram_id=call.from_user.id,
                    daily_digest=False,
                    weekly_digest=True,
                    twitter_category=payload.category
                )
                await repo.subscribe_user_category(user_input)
                await bot.send_message(call.from_user.id, "OK")