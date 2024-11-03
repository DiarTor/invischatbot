import threading
import time

from decouple import config
from telebot import TeleBot

from bot.managers.anonymous_chat import ChatHandler
from bot.managers.callback import CallbackHandler
from bot.managers.nickname import NicknameManager
from bot.managers.start import StartBot

bot = TeleBot(token=config('BOT_TOKEN', cast=str))

start_bot = StartBot(bot)
chat_handler = ChatHandler(bot)
callback_handler = CallbackHandler(bot)
nickname_handler = NicknameManager(bot)
# Register handlers
bot.register_message_handler(start_bot.start, commands=['start'])
bot.register_message_handler(start_bot.link, commands=['link'])
bot.register_message_handler(nickname_handler.set_nickname, commands=['nickname'])
bot.register_message_handler(chat_handler.anonymous_chat, content_types=['text'])
bot.register_callback_query_handler(callback_handler.handle_callback, func=lambda call: True)


def keep_alive():
    while True:
        bot.get_me()  # Pings the API to keep the connection alive
        time.sleep(60)  # Sends a ping every 60 seconds


# Start the keep-alive thread
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
