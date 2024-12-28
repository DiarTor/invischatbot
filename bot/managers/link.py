from decouple import config
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.language import get_response


class LinkManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def link(self, msg: Message):
        user_bot_id = users_collection.find_one({"user_id": msg.from_user.id})['id']
        link = self._generate_link(user_bot_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('greeting.link', link),
            parse_mode='Markdown'
        )
        await self.bot.send_message(
            msg.chat.id,
            get_response('greeting.send_link', link),
            parse_mode='Markdown'
        )

    @staticmethod
    def _generate_link(user_id: str) -> str:
        """Generate a link to the bot for the user."""
        return f"https://t.me/{config('BOT_USERNAME', cast=str)}?start={user_id}"
