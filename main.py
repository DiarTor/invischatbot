from decouple import config
from telebot import TeleBot

from bot.managers.start import start, link
from bot.managers.anonymous_chat import anonymous_chat
from bot.managers.callback import callback_manager
bot = TeleBot(token=config('BOT_TOKEN', cast=str))

bot.register_message_handler(start, commands=['start'], pass_bot=True)
bot.register_message_handler(link, commands=['link'], pass_bot=True)
bot.register_message_handler(anonymous_chat, content_types=['text'], pass_bot=True)
bot.register_callback_query_handler(callback_manager, pass_bot=True, func=lambda call: True)
if __name__ == '__main__':
    bot.infinity_polling()
