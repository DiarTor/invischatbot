from decouple import config
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.date import convert_timestamp_to_date
from bot.utils.language import get_response


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

        user_anny_id = parts[1]
        user_info = users_collection.find_one({"id": user_anny_id})
        if not user_info:
            await self.bot.send_message(user_id, get_response('admin.errors.info.not_found'))

        joined_at = convert_timestamp_to_date(user_info['joined_at'])
        chats_count = self._get_chats_count(user_info['chats'])
        blocks_count = self._get_blocks_count(user_info['blocklist'])

        username = user_info['username']
        first_name = user_info['first_name']
        last_name = user_info['last_name']

        await self.bot.send_message(user_id, get_response('admin.user.info', user_info['user_id'], user_info['id'],
                                                          user_info['nickname'], joined_at, username, first_name,
                                                          last_name, chats_count,
                                                          blocks_count),
                                    parse_mode='Markdown')

    @staticmethod
    def _get_chats_count(chats):
        chats_count = [chat for chat in chats]
        return len(chats_count)

    @staticmethod
    def _get_blocks_count(blocks):
        return len(blocks)
