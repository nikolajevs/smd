import os
from aiogram.types import Message, ContentType
from keyboards.default.markups import *
from loader import dp, db, types, bot
from data import config
from handlers.user.menu import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from datetime import datetime

class SendLabelState(StatesGroup):
    label = State()
    expDate = State()

@dp.message_handler(text=config.send_label_photo)
async def process_send_label(message: Message, state: FSMContext):

    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(cancel_message)
    await message.reply(f"Send label number.", reply_markup=markup)
    await state.set_state(SendLabelState.label.state)

@dp.message_handler(text=cancel_message, state=SendLabelState.label)
async def process_send_label_msg_cancel(message: Message, state: FSMContext):
    await message.answer('Canceled!', reply_markup=home_user_markup())
    await SendLabelState.label.set()   
    await state.finish()

@dp.message_handler(content_types=ContentType.TEXT, state=SendLabelState.label)
async def handle_label_number(message: types.Message, state: FSMContext):
    if str(message.text).isnumeric():
        async with state.proxy() as data:
            data['number'] = message.text
    else:
        await message.answer("Label must be number!", reply_markup=home_user_markup())
        await state.finish()
        return

    await SendLabelState.next()
    await message.answer('Send Exp.Date', reply_markup=cancel_markup())

@dp.message_handler(text=cancel_message, state=SendLabelState.expDate)
async def process_send_label_expDate_cancel(message: Message, state: FSMContext):
    await message.answer('Canceled!', reply_markup=home_user_markup())
    await SendLabelState.expDate.set()   
    await state.finish()

@dp.message_handler(content_types=ContentType.TEXT, state=SendLabelState.expDate)
async def handle_label_expDate(message: types.Message, state: FSMContext):

    expDateUser = datetime.strptime(message.text, "%d/%m/%Y").date()

    async with state.proxy() as data:
        data['expDate'] = expDateUser

    async with state.proxy() as data:
        label = data["number"]
        expDate = data["expDate"]

        db.query('INSERT INTO labels VALUES (?, ?, ?, ?, ?)', (None, message.from_user.id, datetime.now(), label, expDate))


    await message.answer("Label added!", reply_markup=home_user_markup())
    await state.finish()

