"""
    This module contains the UserAdministration class;
    which handles user administration commands for the bot.
    It includes methods for getting user information and banning users, etc...
"""
from datetime import datetime
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.common.data import UserDataManager, BotDataManager, get_user_id
from bot.common.utils import convert_timestamp_to_date
from bot.languages.response import get_response

class UserAdministration:
    """
    Class to handle user administration commands for the bot.
    """
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.user_manager = UserDataManager()
        self.bot_manager = BotDataManager()

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
            return

        user_anon_id = parts[1]
        await self.user_manager.bind_user(await get_user_id(user_anon_id))
        user_info = await self.user_manager.fetch_user()
        if not user_info:
            # If user_anon_id is not found, check if it's a user_id
            await self.user_manager.bind_user(int(user_anon_id))
            user_info = await self.user_manager.fetch_user()
        if not user_info:
            await self.bot.send_message(user_id, get_response('admin.errors.info.not_found'))
            return
        joined_at = convert_timestamp_to_date(user_info.get('metadata', {}).get('joined_at', None), 'datetime')
        chats_count = self._get_chats_count(user_info.get('chatting', {}).get('chats', None))
        blocks_count = self._get_blocks_count(user_info.get('chatting', {}).get('blocklist', None))

        username = user_info.get('profile', {}).get('username', None)
        first_name = user_info.get('profile', {}).get('first_name', None)
        last_name = user_info.get('profile', {}).get('last_name', None)
        nickname = user_info.get('profile', {}).get('nickname', None)
        is_banned = user_info.get('ban_info', {}).get('is_banned', False)
        banned_by = user_info.get('ban_info', {}).get('banned_by', None)
        banned_at = convert_timestamp_to_date(user_info.get('ban_info', {}).get('banned_at', None), 'datetime') if user_info.get('ban_info', {}).get('banned_at', None) else None
        is_bot_off = user_info.get('flags', {}).get('is_bot_off', False)
        user_data = {
            "user_id": user_info.get('user_id'),
            "joined_at": joined_at,
            "chats_count": chats_count,
            "blocks_count": blocks_count,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "nickname": nickname,
            "anon_id": user_info.get('anon_id'),
            "is_banned": is_banned,
            "banned_by": banned_by,
            "banned_at": banned_at,
            "is_bot_off": is_bot_off,
            "is_admin": await self.bot_manager.is_admin(user_info['user_id']),
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
        await self.user_manager.bind_user(await get_user_id(user_anon_id))
        user_info = await self.user_manager.fetch_user()

        if not user_info:
            # If user_anon_id is not found, check if it's a user_id
            await self.user_manager.bind_user(int(user_anon_id))
            user_info = await self.user_manager.fetch_user()

        if not user_info:
            await self.bot.send_message(user_id,
                                        get_response('admin.errors.ban.not_found'))
        if user_info.get('ban_info', {}).get('is_banned', False):
            await self.bot.send_message(user_id,
                                        get_response('admin.errors.ban.already_banned'))
            return
        if await self.bot_manager.is_admin(user_info['user_id']):
            await self.bot.send_message(user_id, get_response('admin.errors.ban.admin_ban'))
            return
        await self.user_manager.update_fields({"ban_info.is_banned": True,
                                                "ban_info.banned_by": user_id,
                                                "ban_info.banned_at": datetime.timestamp(datetime.now())})
        await self.bot_manager.update_ban_list(user_info['user_id'], 'ban')

        username = user_info.get('profile', {}).get('username', None)
        first_name = user_info.get('profile', {}).get('first_name', None)
        last_name = user_info.get('profile', {}).get('last_name', None)
        nickname = user_info.get('profile', {}).get('nickname', None)
        joined_at = convert_timestamp_to_date(user_info.get('metadata', {}).get('joined_at', None), 'datetime')
        if user_anon_id.isdigit():
            user_anon_id = user_info.get('anon_id')
        response_info = {
            'user_id': user_info['user_id'],
            'anon_id': user_anon_id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'nickname': nickname,
            'joined_at': joined_at,
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
        await self.user_manager.bind_user(await get_user_id(user_anon_id))
        user_info = await self.user_manager.fetch_user()

        if not user_info:
            # If user_anon_id is not found, check if it's a user_id
            await self.user_manager.bind_user(int(user_anon_id))
            user_info = await self.user_manager.fetch_user()

        if not user_info:
            await self.bot.send_message(admin_user_id, get_response('admin.errors.unban.not_found'))
            return
        if not user_info.get('ban_info', {}).get('is_banned', False):
            await self.bot.send_message(admin_user_id,
                                        get_response('admin.errors.unban.not_banned'))
            return
        await self.user_manager.update_fields({"ban_info.is_banned": False,
                                                "ban_info.banned_by": None,
                                                "ban_info.banned_at": None})
        await self.bot_manager.update_ban_list(user_info['user_id'], 'unban')

        username = user_info.get('profile', {}).get('username', None)
        first_name = user_info.get('profile', {}).get('first_name', None)
        last_name = user_info.get('profile', {}).get('last_name', None)
        nickname = user_info.get('profile', {}).get('nickname', None)
        joined_at = convert_timestamp_to_date(user_info.get('metadata', {}).get('joined_at', None), 'datetime')
        if user_anon_id.isdigit():
            user_anon_id = user_info.get('anon_id')
        response_info = {
            'user_id': user_info['user_id'],
            'anon_id': user_anon_id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'nickname': nickname,
            'joined_at': joined_at,
            'unbanned_at': convert_timestamp_to_date(datetime.timestamp(datetime.now()), 'datetime'),
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
