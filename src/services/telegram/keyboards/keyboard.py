import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
from typing import List, Sequence
from telebot import types
from telebot.types import InlineKeyboardMarkup
from src.database.models.models import Category

def category_list_button(categories: Sequence[Category]) -> InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()

    for category in categories:
        markup.add(types.InlineKeyboardButton(category.name, callback_data=str(category.id)))

    return markup

def account_list_button(accounts: Sequence[str]) -> InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()

    for account in accounts:
        markup.add(types.InlineKeyboardButton(account, callback_data=account))

    return markup

def time_button() -> InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()

    weekly = types.InlineKeyboardButton("weekly", "weekly")
    daily = types.InlineKeyboardButton("daily", "daily")

    return markup

