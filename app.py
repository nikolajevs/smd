import asyncio
import datetime
from aiogram.types import Message
from aiogram.utils import executor
from handlers.user.menu import *
from loader import dp, db, bot
from data import config
from filters import *
import filters

filters.setup(dp)

@dp.message_handler(commands='start')
async def cmd_start(message: Message):

    user_id = message.from_user.id    
    userExist = db.fetchone(f'SELECT * FROM users WHERE cid = {user_id}')

    if userExist:
        getName = db.fetchones(f'SELECT name FROM users WHERE cid = {user_id}')
        getUserName = db.fetchones(f'SELECT username FROM users WHERE cid = {user_id}')
  
        if getName != message.from_user.full_name:
            db.query(f"UPDATE users SET name = ? WHERE cid = ?",(message.from_user.first_name, user_id))
        if getUserName != message.from_user.username:
            db.query(f"UPDATE users SET username = ? WHERE cid = ?",(message.from_user.username, user_id))
    else :
        db.query('INSERT INTO users VALUES (?, ?, ?, ?, ?)', (None, user_id, datetime.datetime.now(), message.from_user.full_name, message.from_user.username))


    if (message.from_user.id in config.ADMINS):
        await message.answer(f"Hi,<b> {message.from_user.full_name} </b>", reply_markup=admin_home_markup())
    else :
        await message.answer(f"<b>{config.bot_start_greeting}</b> <b>{message.from_user.full_name}</b>\n\n", reply_markup=home_user_markup())


async def main():

    import dateChecker
    asyncio.create_task(dateChecker.start())
    await dp.start_polling(bot)

if __name__ == '__main__':

    asyncio.run(main())