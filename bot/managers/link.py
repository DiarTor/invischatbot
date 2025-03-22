from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.utils import generate_anon_link


class LinkManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def link(self, msg: Message):
        user_bot_id = users_collection.find_one({"user_id": msg.from_user.id})['id']
        link = generate_anon_link(user_bot_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('greeting.link', link),
            parse_mode='Markdown',
            reply_markup=KeyboardMarkupGenerator().share_link_buttons(get_response('greeting.share_link'))
        )
        await self.bot.send_message(
            msg.chat.id,
            get_response('greeting.send_link', link),
            parse_mode='Markdown'
        )
