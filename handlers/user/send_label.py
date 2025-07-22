import datetime
import os
from aiogram.types import Message, ContentType
from keyboards.default.markups import *
from loader import dp, db, types, bot
from data import config
from handlers.user.menu import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from PIL import Image
import pytesseract
from google import genai

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
    async with state.proxy() as data:
        data['expDate'] = message.text

    async with state.proxy() as data:
        label = data["number"]
        expDate = data["expDate"]

        db.query('INSERT INTO labels VALUES (?, ?, ?, ?, ?)', (None, message.from_user.id, datetime.datetime.now(), label, expDate))


    await message.answer("Label added!", reply_markup=home_user_markup())
    await state.finish()


@dp.message_handler(content_types=ContentType.PHOTO, state=SendLabelState.label)
async def handle_label_photo(message: types.Message, state: FSMContext):
        
    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path, os.path.join(os.getcwd(), "img.jpg")))

    image = Image.open(downloaded_file.name)
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    text = pytesseract.image_to_string(image)

    client = genai.Client(api_key="AIzaSyBjRZND0JalSXr1aDCQeXCM8sKndymvbWM")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Send me back Label number and Date(DD/MM/YYYY) in YYYY-MM-DD format without comments: {text}"
    )

    if response.text:
        responseData = response.text.partition(' ')
        label = responseData[0]
        expDate = responseData[2]
        if label.isnumeric():
            db.query('INSERT INTO labels VALUES (?, ?, ?, ?, ?)', (None, message.from_user.id, datetime.datetime.now(), label, expDate))
        else:
            await message.answer("Error reading image!", reply_markup=home_user_markup())
            await state.finish() 
            return
    else:
        await message.answer("Server Busy. Try again...", reply_markup=home_user_markup())
        await state.finish()
        return

    await message.answer(f"{label}\n{expDate}", reply_markup=home_user_markup())
    await state.finish()