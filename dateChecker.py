import asyncio
from data import config
from loader import db, bot, dp
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from handlers.user.menu import *

delete_label_cb = CallbackData('delete_label_cb', 'id', 'action')

async def start():

    while True:
        await asyncio.sleep(10)

        labelData = db.fetchall(f'SELECT * FROM labels ORDER BY date(expDate) ASC Limit 1')
        if len(labelData) == 0: return
        oldestLabel = labelData[0]
        dateFromDB = datetime.strptime(oldestLabel[4], "%Y-%m-%d")
        timeDiff = dateFromDB - datetime.now()

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Delete ❌', callback_data=delete_label_cb.new(id = oldestLabel[0], action="delete_label")))
            
        if dateFromDB < datetime.now():
            for admin in config.ADMINS:
                await bot.send_message(admin, f'<b>Check fridge!</b>\nLabel: {oldestLabel[3]}\nDate: {oldestLabel[4]}', reply_markup=markup)
        elif timedelta(hours=0) < timeDiff <= timedelta(hours=24):
            for admin in config.ADMINS:
                await bot.send_message(admin, f'<b>24 hours left!</b>\nLabel: {oldestLabel[3]}\nDate: {oldestLabel[4]}', reply_markup=markup)
    
@dp.callback_query_handler(delete_label_cb.filter(action='delete_label'))
async def delete_label_callback_handler(query: CallbackQuery, callback_data: dict):

    labelExist = db.fetchall(f"SELECT * FROM labels WHERE id = {callback_data.get('id')}")
    if labelExist:
        db.query(f"DELETE FROM labels WHERE id = {callback_data.get('id')}")
        await query.message.answer("Label deleted ✅", reply_markup=home_user_markup())
    else:
        await query.message.answer("Label does not exist ❌", reply_markup=home_user_markup())