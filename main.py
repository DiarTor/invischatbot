"""
    This is the main file for the bot.
    It initializes the bot and registers all the handlers.
"""
import asyncio

from decouple import config
from telebot.async_telebot import AsyncTeleBot
from bot.database.database import mongo, init_bot_config
from bot.common.utils import logger
from bot.admin.adminstration import Admin
from bot.admin.user_administration import UserAdministration
from bot.managers.callback import CallbackManager
from bot.managers.chat import ChatHandler
from bot.managers.start import StartBot
from bot.common.threads import profile_sync_loop
from bot.managers.support import SupportManager
bot = AsyncTeleBot(token=config('BOT_TOKEN', cast=str), colorful_logs=True, disable_web_page_preview=True)

# Bot Commands Classes
start_bot = StartBot(bot)
chat_handler = ChatHandler(bot)
callback_manager = CallbackManager(bot)
support_manager = SupportManager(bot)

# Admin Commands Classes
administration_handler = Admin(bot)
user_administration_handler = UserAdministration(bot)

# Bot Commands
bot.register_message_handler(start_bot.start, commands=['start'])
# bot.register_message_handler(support_manager.about, commands=['about'])

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
bot.register_callback_query_handler(callback_manager.handle_callback, func=lambda call: True)
bot.register_inline_handler(callback_manager.handle_inline_query, func=lambda call: True)

async def main():
    """Main function to initialize the bot and start polling."""
    await init_bot_config(mongo.bot_collection)
    asyncio.create_task(profile_sync_loop(bot))

    logger.info("🤖 Starting bot...")

    try:
        await bot.polling(none_stop=True)
    finally:
        logger.info("🛑 Bot stopped.")

        # Properly close the bot (cleans up aiohttp session)
        await bot.close_session()
        logger.info("✅ Bot session closed.")

        # Close Mongo
        await mongo.close()
        logger.info("✅ MongoDB connection closed.")



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (asyncio.CancelledError, RuntimeError, ValueError) as e:
        logger.error("🚨 Error: %s", e)
