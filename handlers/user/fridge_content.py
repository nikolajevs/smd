from aiogram.types import Message
from keyboards.default.markups import *
from loader import dp, db
from data import config
from handlers.user.menu import *
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from dateChecker import delete_label_cb

@dp.message_handler(text=config.fridge_content)
async def process_labels(message: Message):
    
    labels_res = db.fetchall('SELECT * FROM labels ORDER BY date(expDate) DESC')

    if len(labels_res) == 0: await message.answer('No labels 🚫', reply_markup=home_user_markup())
    else: await show_labels(message, labels_res)


async def show_labels(message, labels_res):

    last_msg = ''

    for label in labels_res:

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Delete ❌', callback_data=delete_label_cb.new(id = label[0], action="delete_label")))
            
        last_msg += f'# <code>{label[0]}</code>\n'
        last_msg += f'<b>Label: {label[3]}</b>\n'
        last_msg += f'<b>Date: {label[4]}</b>\n\n'

        await message.answer(last_msg, reply_markup=markup)
        last_msg = ''