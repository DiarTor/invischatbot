from telebot import TeleBot
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.language import get_response


class NicknameManager:
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def set_nickname(self, msg: Message):
        """Set a Nickname when the user sends /nickname command."""
        current_nickname = users_collection.find_one({'user_id': msg.from_user.id})['nickname']
        self.bot.send_message(msg.chat.id, get_response('nickname.ask_nickname', current_nickname),
                              parse_mode='Markdown')
        self.bot.register_next_step_handler(msg, self._save_nickname)

    def _save_nickname(self, msg: Message):
        """Save the user's nickname after they provide it."""
        nickname = msg.text
        user_id = msg.from_user.id

        # Store the user with their nickname
        self._store_user_data(user_id, nickname=nickname)

        self.bot.send_message(msg.chat.id, get_response('nickname.nickname_was_set', nickname), parse_mode='Markdown')

    @staticmethod
    def _store_user_data(user_id: int, nickname: str):
        users_collection.update_one({'user_id': user_id}, {'$set': {'nickname': nickname}})
