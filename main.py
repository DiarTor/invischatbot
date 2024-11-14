import asyncio

from decouple import config
from telebot.async_telebot import AsyncTeleBot

from bot.admin.bot_administarion import AdminManager
from bot.managers.chat import ChatHandler
from bot.managers.block import BlockUserManager
from bot.managers.callback import CallbackHandler
from bot.managers.nickname import NicknameManager
from bot.managers.start import StartBot

bot = AsyncTeleBot(token=config('BOT_TOKEN', cast=str), colorful_logs=True)

# Bot Commands Classes
start_bot = StartBot(bot)
chat_handler = ChatHandler(bot)
callback_handler = CallbackHandler(bot)
nickname_handler = NicknameManager(bot)
block_user_handler = BlockUserManager(bot)

# Admin Commands Classes
admin_handler = AdminManager(bot)

# Bot Commands
bot.register_message_handler(start_bot.start, commands=['start'])
bot.register_message_handler(nickname_handler.set_nickname, commands=['nickname'])

# Admin Commands
bot.register_message_handler(admin_handler.get_bot_status, commands=['status'])

# Content Type Handlers
bot.register_message_handler(chat_handler.anonymous_chat, content_types=['text'])

# CallBack Handlers
bot.register_callback_query_handler(callback_handler.handle_callback, func=lambda call: True)

if __name__ == '__main__':
    asyncio.run(bot.infinity_polling())
