from aiogram.types import Message, ContentType
from keyboards.default.markups import *
from loader import dp, db, types, bot
from data import config
from handlers.user.menu import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from datetime import datetime
import os
import pytesseract
import cv2
import numpy as np
import re
from dateutil.parser import parse as parse_date

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

def extract_text_from_label(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Резкость
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)

    # Увеличение и двоичная фильтрация
    resized = cv2.resize(sharp, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(resized, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR
    config = r'--oem 3 --psm 6 -c tessedit_char_blacklist=|~`@#$%^&*()_={}[]<> --tessdata-dir "/usr/share/tesseract-ocr/5/tessdata"'
    text = pytesseract.image_to_string(thresh, config=config)
    return text

def extract_text_from_label(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Резкость
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)

    # Увеличение и бинаризация
    resized = cv2.resize(sharp, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(resized, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR
    config = r'--oem 3 --psm 6 -c tessedit_char_blacklist=|~`@#$%^&*()_={}[]<> --tessdata-dir "/usr/share/tesseract-ocr/5/tessdata"'
    text = pytesseract.image_to_string(thresh, config=config)
    return text

@dp.message_handler(content_types=ContentType.PHOTO, state=SendLabelState.label)
async def handle_label_photo(message: types.Message, state: FSMContext):
    file_path = os.path.join(os.getcwd(), "img.jpg")
    try:
        file_id = message.photo[-1].file_id
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path)

        with open(file_path, "wb") as f:
            f.write(downloaded_file.read())

        # Указываем путь к tesseract
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

        text = extract_text_from_label(file_path)

        # Улучшенные регулярки
        label_match = re.search(r'(Label|LBL)[^\d]*(\d{4,})', text, re.IGNORECASE)
        exp_match = re.search(r'(Exp|Expiry)[^\d]*(\d{1,2}[./\\-]\d{1,2}[./\\-]\d{2,4})', text, re.IGNORECASE)

        if label_match and exp_match:
            label = label_match.group(2)
            raw_date = exp_match.group(2).replace('.', '/').replace('-', '/')

            try:
                exp_date_obj = parse_date(raw_date, dayfirst=True)
                exp_date = exp_date_obj.strftime("%Y-%m-%d")
            except Exception:
                await message.answer("Не удалось распознать дату.", reply_markup=home_user_markup())
                await state.finish()
                return

            async with state.proxy() as data:
                data['label'] = label
                data['expDate'] = exp_date

            await SendLabelState.confirm.set()
            await message.answer(f"Label: {label}\nExp.Date: {exp_date}", reply_markup=submit_markup())
        else:
            await message.answer("Не удалось найти Label или Exp. Date.", reply_markup=home_user_markup())
            await state.finish()

    except Exception as e:
        await message.answer("Ошибка при обработке изображения.", reply_markup=home_user_markup())
        print(f"[OCR ERROR] {e}")
        await state.finish()

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    
@dp.message_handler(text=all_right_message, state=SendLabelState.confirm)
async def handle_label_photo_ok(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        label = data["label"]
        expDate = data["expDate"]

        labelExists = db.fetchone('SELECT * FROM labels WHERE label = ?', (label,))

        if labelExists:
            await message.answer("Label already exists!", reply_markup=home_user_markup())
            await state.finish()
            return
        else:
            db.query('INSERT INTO labels VALUES (?, ?, ?, ?, ?)', (None, message.from_user.id, datetime.now(), label, expDate))

            await message.answer("Label added!", reply_markup=home_user_markup())
            await state.finish()

@dp.message_handler(text=cancel_message, state=SendLabelState.confirm)
async def process_label_txt_cancel(message: Message, state: FSMContext):
    await message.answer('Canceled!', reply_markup=home_user_markup())
    await SendLabelState.confirm.set()   
    await state.finish()