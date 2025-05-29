"""
This file contains the main adminstration class and its methods.
"""
from telebot.async_telebot import AsyncTeleBot

from telebot.types import Message

from bot.admin.keyboard import Keyboard
from bot.common.database_utils import is_admin, get_admins
from bot.common.date import convert_timestamp_to_date
from bot.languages.response import get_response
from bot.common.database_utils import fetch_user_data_by_id

class Admin:
    """
    Admin class to handle admin operations.
    """
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def main(self, msg: Message):
        """
        Main admin panel
        :param msg: Message object
        """
        if not is_admin(msg.from_user.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.panel',
                                                              name=msg.from_user.first_name),
                                        reply_markup=Keyboard().main_panel(), parse_mode='Markdown')

    async def announce_new_user(self, user_id: int):
        """
        Announce new user to all admins
        :param user_id: ID of the new user
        """
        user_data = fetch_user_data_by_id(user_id)
        stats_data = {
            "first_name": user_data.get('first_name', 'N/A'),
            "last_name": user_data.get('last_name', 'N/A'),
            "id": str(user_data.get('id', 'N/A')),
            "username": user_data.get('username', 'N/A'),
            "user_id": int(user_data.get('user_id', 0)),
            "nickname": user_data.get('nickname', 'N/A'),
            "joined_at": convert_timestamp_to_date(user_data['joined_at'], "datetime"),

        }
        for admin in await get_admins():
            await self.bot.send_message(
                admin,
                get_response('admin.stats.new_user',
                             **stats_data),
                parse_mode='Markdown'
            )

    async def ahelp(self, msg: Message):
        """
        Help command for admin
        :param msg: Message object
        """
        if not is_admin(msg.from_user.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.help'), parse_mode='Markdown')
