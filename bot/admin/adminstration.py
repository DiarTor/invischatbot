from decouple import config
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.admin.keyboard import Keyboard
from bot.common.database_utils import is_admin
from bot.database.database import bot_collection
from bot.languages.response import get_response


class Admin:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def main(self, msg: Message):
        if not is_admin(msg.from_user.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.panel', name=msg.from_user.first_name),
                                    reply_markup=Keyboard().main_panel(),parse_mode='Markdown')

