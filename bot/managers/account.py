from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.date import convert_timestamp_to_date
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.user_data import get_user


class AccountManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def account(self, msg: Message):
        """ send the response text"""
        user_data = get_user(msg.chat.id)
        joined_at = convert_timestamp_to_date(user_data['joined_at'])
        await self.bot.send_message(msg.chat.id, get_response('account.show', user_data['id'],
                                                              user_data['nickname'], joined_at), parse_mode='Markdown',
                                    reply_markup=KeyboardMarkupGenerator().account_buttons())

    @staticmethod
    def get_account_response(msg: Message):
        """ return the response text"""
        user_data = get_user(msg.chat.id)
        joined_at = convert_timestamp_to_date(user_data['joined_at'])
        return get_response('account.show', user_data['id'],
                            user_data['nickname'], joined_at)
