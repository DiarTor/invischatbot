import asyncio

from decouple import config
from telebot.async_telebot import AsyncTeleBot

from bot.admin.adminstration import Admin
from bot.admin.bot_administration import BotAdministration
from bot.admin.user_administration import UserAdministration
from bot.managers.block import BlockUserManager
from bot.managers.callback import CallbackHandler
from bot.managers.chat import ChatHandler
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
administration_handler = Admin(bot)
user_administration_handler = UserAdministration(bot)

# Bot Commands
bot.register_message_handler(start_bot.start, commands=['start'])

# Admin Commands
bot.register_message_handler(administration_handler.main, commands=['admin'])
bot.register_message_handler(user_administration_handler.get_user_info, commands=['info'])

# Content Type Handlers
bot.register_message_handler(chat_handler.anonymous_chat,
                             content_types=['text', 'audio', 'photo', 'voice', 'document', 'video', 'animation',
                                            'sticker', 'video_note'])

# CallBack Handlers
bot.register_callback_query_handler(callback_handler.handle_callback, func=lambda call: True)
bot.register_inline_handler(callback_handler.handle_inline_query, func=lambda call: True)

if __name__ == '__main__':
    asyncio.run(bot.infinity_polling())
