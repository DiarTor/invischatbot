"""Manager for handling user settings, specifically the bot status."""
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.data import UserDataManager
class SettingsManager:
    """Manager for handling user settings, specifically the bot status."""
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.user_manager = UserDataManager()

    async def change_bot_status(self, callback: CallbackQuery):
        """Change the bot status for the user."""
        await self.user_manager.bind_user(callback.message.chat.id)
        user_id = callback.message.chat.id
        if await self.user_manager.is_bot_disabled() is True:
            await self.user_manager.toggle_flag("is_bot_off", False)
            await self.bot.answer_callback_query(callback_query_id=callback.id,
                                                 text=get_response("account.bot_status.self.status_changed.on", status="روشن 😁"),
                                                show_alert=True,
                                                cache_time=0)
            await self.bot.edit_message_reply_markup(message_id=callback.message.id, chat_id=user_id,
                                                     reply_markup=KeyboardMarkupGenerator().account_buttons())
        else:
            await self.user_manager.toggle_flag("is_bot_off", True)
            await self.bot.answer_callback_query(callback_query_id=callback.id,
                                                text=get_response("account.bot_status.self.status_changed.off", status="خاموش😴"),
                                                show_alert=True,
                                                cache_time=0)
            await self.bot.edit_message_reply_markup(message_id=callback.message.id,
                                                    chat_id=user_id,
                                                    reply_markup=KeyboardMarkupGenerator().account_buttons(is_bot_off=True))
