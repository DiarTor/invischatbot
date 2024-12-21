from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.managers.account import AccountManager
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.user_data import is_bot_status_off, update_user_field


class SettingsManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def change_bot_status(self, callback: CallbackQuery):
        user_id = callback.message.chat.id
        if is_bot_status_off(user_id):
            update_user_field(user_id, 'is_bot_off', False)
            await self.bot.answer_callback_query(callback_query_id=callback.id,
                                                 text=get_response("account.bot_status.self.status_changed", "روشن 😁"))
            await self.bot.edit_message_text(chat_id=user_id, message_id=callback.message.id,
                                             text=AccountManager.get_account_response(callback.message),
                                             reply_markup=KeyboardMarkupGenerator().account_buttons(),
                                             parse_mode='Markdown')
        else:
            update_user_field(user_id, 'is_bot_off', True)
            await self.bot.answer_callback_query(callback_query_id=callback.id,
                                                 text=get_response("account.bot_status.self.status_changed", "خاموش😴"))
            await self.bot.edit_message_text(chat_id=user_id, message_id=callback.message.id,
                                             text=AccountManager.get_account_response(callback.message),
                                             reply_markup=KeyboardMarkupGenerator().account_buttons(True),
                                             parse_mode='Markdown')
