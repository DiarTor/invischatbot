from telebot.async_telebot import AsyncTeleBot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.admin.keyboard import Keyboard
from bot.common.database_utils import is_admin, get_admins
from bot.common.date import convert_timestamp_to_date
from bot.database.database import users_collection
from bot.languages.response import get_response


class Admin:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def main(self, msg: Message):
        if not is_admin(msg.from_user.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.panel', name=msg.from_user.first_name),
                                    reply_markup=Keyboard().main_panel(), parse_mode='Markdown')

    async def announce_new_user(self, msg: Message, user_id: int):
        user_data = users_collection.find_one({'user_id': user_id})
        stats_data = {
            "first_name": user_data['first_name'],
            "last_name": user_data['last_name'],
            "id": user_data['id'],
            "username": user_data['username'],
            "user_id": user_id,
            "nickname": user_data['nickname'],
            "joined_at": convert_timestamp_to_date(user_data['joined_at'], "datetime"),

        }
        for admin in await get_admins():
            await self.bot.send_message(
                admin,
                get_response('admin.stats.new_user',
                             **stats_data),
                parse_mode='Markdown'
            )
