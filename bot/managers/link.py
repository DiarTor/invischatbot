from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.utils import generate_anon_link
from decouple import config
from bot.common.database_utils import update_user_fields
from bot.common.utils import create_unique_id
class LinkManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.bot_username = config('BOT_USERNAME', default='')

    async def link(self, msg: Message):
        user_bot_id = users_collection.find_one({"user_id": msg.from_user.id})['id']
        link: str = generate_anon_link(user_bot_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.link', link=link),
            parse_mode='HTML',
            reply_markup=KeyboardMarkupGenerator().share_link_buttons(
                get_response('link.share_link'), link)
        )
    async def regenerate_link(self, msg: Message):
        """Regenerate the anonymous link for the user."""
        new_id = create_unique_id()
        await update_user_fields(
            msg.chat.id,
            'id',
            new_id
        )
        new_link: str = generate_anon_link(new_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.regenerate_link.regenerated', link=new_link),
            parse_mode='HTML',
            reply_markup=KeyboardMarkupGenerator().share_link_buttons(
                get_response('link.share_link'), new_link)
        )
