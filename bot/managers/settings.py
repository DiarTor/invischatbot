from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.managers.account import AccountManager
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.user import is_bot_status_off
from bot.common.database_utils import update_user_fields


class SettingsManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def change_bot_status(self, callback: CallbackQuery):
        user_id = callback.message.chat.id
        if is_bot_status_off(user_id):
            await update_user_fields(user_id, 'is_bot_off', False)
            await self.bot.answer_callback_query(callback_query_id=callback.id,
                                                 text=get_response("account.bot_status.self.status_changed", status="روشن 😁"))
            await self.bot.edit_message_reply_markup(message_id=callback.message.id, chat_id=user_id,
                                                     reply_markup=KeyboardMarkupGenerator().account_buttons())
        else:
            await update_user_fields(user_id, 'is_bot_off', True)
            await self.bot.answer_callback_query(callback_query_id=callback.id,
                                                 text=get_response("account.bot_status.self.status_changed", status="خاموش😴"))
            await self.bot.edit_message_reply_markup(message_id=callback.message.id, chat_id=user_id,
                                                     reply_markup=KeyboardMarkupGenerator().account_buttons(is_bot_off=True))
