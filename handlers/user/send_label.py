from aiogram.types import Message, ContentType
from keyboards.default.markups import *
from loader import dp, db, types, bot
from data import config
from handlers.user.menu import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from datetime import datetime
import os
from PIL import Image
import pytesseract
from google import genai

class SendLabelState(StatesGroup):
    label = State()
    expDate = State()
    confirm = State()

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
        labelExists = db.fetchone(f'SELECT * FROM labels WHERE label = {message.text}')
        if labelExists:
            await message.answer("Label already exists!", reply_markup=home_user_markup())
            await state.finish()
            return
        else:
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

    expDateUser = datetime.now().date()

    try:
        expDateUser = datetime.strptime(message.text, "%d/%m/%Y").date()    
    except:
        pass    

    try:
        expDateUser = datetime.strptime(message.text, "%d.%m.%Y").date()
    except:
        pass   

    try:
        expDateUser = datetime.strptime(message.text, "%d-%m-%Y").date()
    except:
        pass    

    try:
        expDateUser = datetime.strptime(message.text, "%d\%m\%Y").date()
    except:
        pass    

    async with state.proxy() as data:
        data['expDate'] = expDateUser

    async with state.proxy() as data:
        label = data["number"]
        expDate = data["expDate"]

        db.query('INSERT INTO labels VALUES (?, ?, ?, ?, ?)', (None, message.from_user.id, datetime.now(), label, expDate))

    await message.answer("Label added ✅", reply_markup=home_user_markup())
    await state.finish()

@dp.message_handler(content_types=ContentType.PHOTO, state=SendLabelState.label)
async def handle_label_photo(message: types.Message, state: FSMContext):
        
    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path, os.path.join(os.getcwd(), "img.jpg")))
    image = Image.open(downloaded_file.name)
    pytesseract.pytesseract.tesseract_cmd = '/data/data/ru.iiec.pydroid3/files/tesseract'
    tessdata_dir_config = '--tessdata-dir "/storage/emulated/0/tessdata"'
    text = pytesseract.image_to_string(image, lang='eng', config=tessdata_dir_config)
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
            async with state.proxy() as data:
                data['label'] = label
                data['expDate'] = expDate

            await SendLabelState.confirm.set()
            await message.answer(f"Label: {label}\nExp.Date: {expDate}", reply_markup=submit_markup())
        else:
            await message.answer("Error reading image!", reply_markup=home_user_markup())
            await state.finish() 
            return
    else:
        await message.answer("Server Busy. Try again...", reply_markup=home_user_markup())
        await state.finish()
        return
    
@dp.message_handler(text=all_right_message, state=SendLabelState.confirm)
async def handle_label_photo_ok(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        label = data["label"]
        expDate = data["expDate"]

    db.query('INSERT INTO labels VALUES (?, ?, ?, ?, ?)', (None, message.from_user.id, datetime.now(), label, expDate))

    await message.answer("Label added!", reply_markup=home_user_markup())
    await state.finish()