from decouple import config
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.database.database import users_collection
from bot.common.date import convert_timestamp_to_date
from bot.languages.response import get_response


class UserAdministration:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.admin = config("ADMIN", cast=int)

    async def get_user_info(self, msg: Message):
        user_id = msg.from_user.id
        if not user_id == self.admin:
            return
        parts = msg.text.split()
        if not len(parts) == 2:
            await self.bot.send_message(user_id, get_response('admin.errors.info.wrong_format'))

        user_anon_id = parts[1]
        user_info = users_collection.find_one({"id": user_anon_id})
        if not user_info:
            await self.bot.send_message(user_id, get_response('admin.errors.info.not_found'))

        joined_at = convert_timestamp_to_date(user_info['joined_at'])
        chats_count = self._get_chats_count(user_info['chats'])
        blocks_count = self._get_blocks_count(user_info['blocklist'])

        username = user_info['username']
        first_name = user_info['first_name']
        last_name = user_info['last_name']

        user_data = {
            "user_id": user_id,
            "joined_at": joined_at,
            "chats_count": chats_count,
            "blocks_count": blocks_count,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "nickname": user_info['nickname'],
            "anon_id": user_anon_id,
        }

        await self.bot.send_message(user_id, get_response('admin.user.info', **user_data),parse_mode='Markdown')

    @staticmethod
    def _get_chats_count(chats):
        chats_count = [chat for chat in chats]
        return len(chats_count)

    @staticmethod
    def _get_blocks_count(blocks):
        return len(blocks)
