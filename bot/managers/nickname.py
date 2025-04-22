import random

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.chat_utils import close_chats
from bot.common.database_utils import update_user_fields
from bot.common.validators import NicknameValidator


class NicknameManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def set_nickname(self, msg: Message):
        """Set a Nickname when the user sends /nickname command."""
        user_data = users_collection.find_one_and_update({'user_id': msg.chat.id},
                                                         {'$set': {'awaiting_nickname': True}})
        current_first_name = msg.chat.first_name
        close_chats(msg.chat.id, True)
        await self.bot.send_message(msg.chat.id,
                                    get_response('nickname.ask_nickname', current_nickname=user_data['nickname'], current_firstname=current_first_name),
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
            update_user_fields(user_id, "nickname", nickname)
            update_user_fields(user_id, "awaiting_nickname", False)
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
            )

    @staticmethod
    def get_set_nickname_response(msg: Message):
        """return set nickname response"""
        user_data = users_collection.find_one_and_update({'user_id': msg.chat.id},
                                                         {'$set': {'awaiting_nickname': True}})
        current_first_name = msg.chat.first_name
        return get_response('nickname.ask_nickname', current_nickname=user_data['nickname'], current_firstname=current_first_name)

    @staticmethod
    def generate_random_nickname():
        # List of random English names
        random_names = [
            "John", "Alice", "Bob", "Charlie", "Daisy", "Eve", "Frank",
            "Grace", "Hannah", "Ivy", "Jack", "Kate", "Liam", "Mia",
            "Noah", "Olivia", "Paul", "Quinn", "Ryan", "Sophie", "Tom",
            "Uma", "Victor", "Wendy", "Xander", "Yara", "Zack", "Ali", "Ahmad"
        ]

        # Pick a random name from the list
        random_name = random.choice(random_names)
        # Return the nickname
        return random_name
