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