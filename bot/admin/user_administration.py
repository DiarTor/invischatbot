"""
    This module contains the UserAdministration class;
    which handles user administration commands for the bot.
    It includes methods for getting user information and banning users, etc...
"""
from datetime import datetime
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.common.data import UserDataManager, BotDataManager, get_user_id
from bot.database.database import mongo
from bot.common.utils import convert_timestamp_to_date
from bot.languages.response import get_response

class UserAdministration:
    """
    Class to handle user administration commands for the bot.
    """
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.user_manager = UserDataManager(mongo.users_collection)
        self.bot_manager = BotDataManager(mongo.bot_collection)

    async def get_user_info(self, msg: Message):
        """
        Get user information by user_anon_id.
        :param msg: Message object containing the command and user_anon_id.
        """
        user_id = msg.from_user.id
        if not await self.bot_manager.is_admin(user_id):
            return
        parts = msg.text.split()
        if not len(parts) == 2:
            await self.bot.send_message(user_id, get_response('admin.errors.info.wrong_format'))

        user_anon_id = parts[1]
        await self.user_manager.bind_user(get_user_id(user_anon_id))
        user_info = await self.user_manager.fetch_user()
        if not user_info:
            # If user_anon_id is not found, check if it's a user_id
            self.user_manager.bind_user(int(user_anon_id))
            user_info = await self.user_manager.fetch_user()
        if not user_info:
            await self.bot.send_message(user_id, get_response('admin.errors.info.not_found'))
            return
        joined_at = convert_timestamp_to_date(user_info['joined_at'])
        chats_count = self._get_chats_count(user_info['chats'])
        blocks_count = self._get_blocks_count(user_info['blocklist'])

        username = user_info['username']
        first_name = user_info['first_name']
        last_name = user_info['last_name']

        user_data = {
            "user_id": user_info.get('user_id'),
            "joined_at": joined_at,
            "chats_count": chats_count,
            "blocks_count": blocks_count,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "nickname": user_info['nickname'],
            "anon_id": user_info.get('id'),
            "is_banned": user_info.get('is_banned'),
            "banned_by": user_info.get('banned_by'),
            "banned_at": user_info.get('banned_at'),
            "is_bot_off": user_info.get('is_bot_off'),
            "is_admin": self.bot_manager.is_admin(user_info['user_id']),
        }

        await self.bot.send_message(user_id, get_response('admin.user.info', **user_data)
                                    ,parse_mode='Markdown')

    async def ban_user(self, msg: Message):
        """
        Ban a user by user_anon_id.
        :param msg: Message object containing the command and user_anon_id.
        """

        user_id = msg.from_user.id
        if not await self.bot_manager.is_admin(user_id):
            await self.bot.send_message(user_id, get_response('errors.no_active_chat'))
            return
        parts = msg.text.split()
        if not len(parts) == 2:
            await self.bot.send_message(user_id,
                                        get_response('admin.errors.ban.wrong_format'))
            return

        user_anon_id = parts[1]
        self.user_manager.bind_user(get_user_id(user_anon_id))
        user_info = self.user_manager.fetch_user()
        if not user_info:
            await self.bot.send_message(user_id,
                                        get_response('admin.errors.ban.not_found'))
        if user_info.get('is_banned'):
            await self.bot.send_message(user_id,
                                        get_response('admin.errors.ban.already_banned'))
            return
        if self.bot_manager.is_admin(user_info['user_id']):
            await self.bot.send_message(user_id, get_response('admin.errors.ban.admin_ban'))
            return
        await self.user_manager.update_fields({"is_banned": True,
                                                "banned_by": user_id,
                                                "banned_at": datetime.timestamp(datetime.now())})
        await self.bot_manager.update_ban_list(user_info['user_id'], 'ban')
        response_info = {
            'user_id': user_info['user_id'],
            'anon_id': user_anon_id,
            'first_name': user_info['first_name'],
            'last_name': user_info['last_name'],
            'username': user_info['username'],
            'nickname': user_info['nickname'],
            'joined_at': convert_timestamp_to_date(user_info['joined_at'], ),
            'banned_at': convert_timestamp_to_date(datetime.timestamp(datetime.now()), 'datetime'),
        }

        for admin in await self.bot_manager.get_admins():
            await self.bot.send_message(
                admin,
                get_response('admin.user.ban.success', **response_info),
                parse_mode='Markdown'
            )
        await self.bot.send_message(user_info.get('user_id'), get_response('account.ban.banned'),
                                    parse_mode='Markdown')

    async def unban_user(self, msg: Message):
        """
        Unban a user by user_anon_id.
        :param msg: Message object containing the command and user_anon_id.
        """
        admin_user_id = msg.from_user.id
        if not await self.bot_manager.is_admin(admin_user_id):
            await self.bot.send_message(admin_user_id,
                                        get_response('errors.no_active_chat'))
            return
        parts = msg.text.split()
        if not len(parts) == 2:
            await self.bot.send_message(admin_user_id,
                                        get_response('admin.errors.unban.wrong_format'))

        user_anon_id = parts[1]
        await self.user_manager.bind_user(get_user_id(user_anon_id))
        user_info = self.user_manager.fetch_user()
        if not user_info:
            await self.bot.send_message(admin_user_id, get_response('admin.errors.unban.not_found'))
            return
        if not user_info.get('is_banned'):
            await self.bot.send_message(admin_user_id,
                                        get_response('admin.errors.unban.not_banned'))
            return
        await self.user_manager.update_fields({"is_banned": False, "banned_by": None,
                                                   "banned_at": None})
        await self.bot_manager.update_ban_list(user_info['user_id'], 'unban')
        response_info = {
            'user_id': user_info['user_id'],
            'anon_id': user_anon_id,
            'first_name': user_info['first_name'],
            'last_name': user_info['last_name'],
            'username': user_info['username'],
            'nickname': user_info['nickname'],
            'joined_at': convert_timestamp_to_date(user_info['joined_at'], ),
            'unbanned_at': convert_timestamp_to_date(datetime.timestamp(datetime.now()), 
                                                    'datetime'),
        }

        for admin in await self.bot_manager.get_admins():
            await self.bot.send_message(
                admin,
                get_response('admin.user.unban.success', **response_info),
                parse_mode='Markdown'
            )
        await self.bot.send_message(user_info.get('user_id'), get_response('account.ban.unbanned'),
                                    parse_mode='Markdown')

    @staticmethod
    def _get_chats_count(chats):
        chats_count = [chat for chat in chats]
        return len(chats_count)

    @staticmethod
    def _get_blocks_count(blocks):
        return len(blocks)
