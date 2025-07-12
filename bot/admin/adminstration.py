"""
This file contains the main adminstration class and its methods.
"""
from telebot.async_telebot import AsyncTeleBot

from telebot.types import Message

from bot.admin.keyboard import Keyboard
from bot.common.data import BotDataManager, UserDataManager
from bot.common.utils import convert_timestamp_to_date
from bot.languages.response import get_response

class Admin:
    """
    Admin class to handle admin operations.
    """
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.bot_manager = BotDataManager()
        self.user_manager = UserDataManager()

    async def main(self, msg: Message):
        """
        Main admin panel
        :param msg: Message object
        """
        if not await self.bot_manager.is_admin(msg.from_user.id):
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
        await self.user_manager.bind_user(user_id)
        user_data = await self.user_manager.fetch_user()
        stats_data = {
            "first_name": user_data.get('profile', 'N/A').get('first_name', 'N/A'),
            "last_name": user_data.get('profile', 'N/A').get('last_name', 'N/A'),
            "anon_id": str(user_data.get('anon_id', 'N/A')),
            "username": user_data.get('profile', 'N/A').get('username', 'N/A'),
            "user_id": int(user_data.get('user_id', 0)),
            "nickname": user_data.get('profile', 'N/A').get('nickname', 'N/A'),
            "joined_at": convert_timestamp_to_date(user_data.get('metadata',
                                                                []).get('joined_at', None),
                                                                "datetime"),

        }
        for admin in await self.bot_manager.get_admins():
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
        if not await self.bot_manager.is_admin(msg.from_user.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.help'), parse_mode='Markdown')
