"""
    This is the main file for the bot.
    It initializes the bot and registers all the handlers.
"""
import asyncio
import logging
import colorlog

from decouple import config
from telebot.async_telebot import AsyncTeleBot

from bot.admin.adminstration import Admin
from bot.admin.user_administration import UserAdministration
from bot.managers.block import BlockUserManager
from bot.managers.callback import CallbackHandler
from bot.managers.chat import ChatHandler
from bot.managers.nickname import NicknameManager
from bot.managers.start import StartBot
from bot.database.database import init_bot_config
# Logging Configuration
def setup_logger():
    """Sets up the logger with color support."""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))
    local_logger = colorlog.getLogger()
    local_logger.addHandler(handler)
    local_logger.setLevel(logging.INFO)  # Set to DEBUG for detailed logs
    return local_logger

logger = setup_logger()

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
bot.register_message_handler(administration_handler.ahelp, commands=['ahelp'])
bot.register_message_handler(administration_handler.main, commands=['admin'])
bot.register_message_handler(user_administration_handler.get_user_info, commands=['info'])
bot.register_message_handler(user_administration_handler.ban_user, commands=['ban'])
bot.register_message_handler(user_administration_handler.unban_user, commands=['unban'])

# Content Type Handlers
bot.register_message_handler(chat_handler.anonymous_chat,
                             content_types=['text', 'audio', 'photo', 'voice', 'document',
                                            'video', 'animation', 'sticker', 'video_note'])

# CallBack Handlers
bot.register_callback_query_handler(callback_handler.handle_callback, func=lambda call: True)
bot.register_inline_handler(callback_handler.handle_inline_query, func=lambda call: True)

if __name__ == '__main__':
    try:
        init_bot_config()  # Ensure default config is set

        logger.info("Starting bot")
        asyncio.run(bot.polling(none_stop=True))
        logger.info("Bot Stopped")
    except (asyncio.CancelledError, RuntimeError, ValueError) as e:
        logger.error("Error: %s", e)

