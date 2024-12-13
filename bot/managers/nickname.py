from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.user_data import reset_replying_state, close_existing_chats
from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.validators import NicknameValidator


class NicknameManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def set_nickname(self, msg: Message):
        """Set a Nickname when the user sends /nickname command."""
        user_data = users_collection.find_one_and_update({'user_id': msg.chat.id},
                                                         {'$set': {'awaiting_nickname': True}})
        current_first_name = msg.chat.first_name
        reset_replying_state(msg.chat.id)
        close_existing_chats(msg.chat.id)
        await self.bot.send_message(msg.chat.id,
                                    get_response('nickname.ask_nickname', user_data['nickname'], current_first_name),
                                    parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def save_nickname(self, msg: Message):
        """Save the user's nickname after they provide it."""
        user_id = msg.from_user.id
        nickname = msg.text.strip()

        # Validate the nickname
        validator = NicknameValidator()
        is_valid, validation_message = validator.validate_nickname(nickname)

        if is_valid:
            # Proceed to store the user data if the nickname is valid
            self._store_user_data(user_id, nickname=nickname)
            users_collection.update_one({'user_id': user_id}, {'$set': {'awaiting_nickname': False}})
            await self.bot.send_message(
                msg.chat.id,
                get_response('nickname.nickname_was_set', nickname),
                parse_mode='Markdown',
                reply_markup=KeyboardMarkupGenerator().main_buttons()
            )
        else:
            # Notify the user about the invalid nickname
            await self.bot.send_message(
                msg.chat.id,
                f"{validation_message}",
                parse_mode='Markdown'
            )

    @staticmethod
    def _store_user_data(user_id: int, nickname: str):
        users_collection.update_one({'user_id': user_id}, {'$set': {'nickname': nickname}})
