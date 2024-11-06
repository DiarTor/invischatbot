from telebot import TeleBot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.language import get_response


class NicknameManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def set_nickname(self, msg: Message):
        """Set a Nickname when the user sends /nickname command."""
        user_data = users_collection.find_one_and_update({'user_id': msg.from_user.id}, {'$set': {'awaiting_nickname': True}})
        await self.bot.send_message(msg.chat.id, get_response('nickname.ask_nickname', user_data['nickname']),
                              parse_mode='Markdown')

    async def save_nickname(self, msg: Message):
        """Save the user's nickname after they provide it."""
        nickname = msg.text
        user_id = msg.from_user.id

        # Store the user with their nickname
        self._store_user_data(user_id, nickname=nickname)
        users_collection.update_one({'user_id': user_id}, {'$set': {'awaiting_nickname': False}})
        await self.bot.send_message(msg.chat.id, get_response('nickname.nickname_was_set', nickname), parse_mode='Markdown')

    @staticmethod
    def _store_user_data(user_id: int, nickname: str):
        users_collection.update_one({'user_id': user_id}, {'$set': {'nickname': nickname}})
