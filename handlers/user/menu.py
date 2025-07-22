from aiogram.types import ReplyKeyboardMarkup
from data import config

def home_user_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(config.send_label_photo)
    markup.add(config.fridge_content)
    return markup

def admin_home_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(config.send_label_photo)
    markup.add(config.fridge_content)
    return markup
