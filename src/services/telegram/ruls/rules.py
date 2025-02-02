from telebot.types import Message

def is_follow_category(message: Message) -> bool:
    return message.text == "Follow Category"

def is_follow_account(message: Message) -> bool:
    return message.text == "Follow Account"
