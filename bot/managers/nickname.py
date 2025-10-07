import random

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.validators import AccountValidator
from bot.common.data import UserDataManager

class NicknameManager:
    """Manager for handling user nicknames in the bot."""
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.user_manager = UserDataManager()

    async def set_nickname(self, msg: Message):
        """Set a Nickname for the user."""
        await self.user_manager.bind_user(msg.from_user.id)
        await self.user_manager.toggle_flag('awaiting_nickname', True)
        current_nickname = await self.user_manager.fetch_user().get('profile',
                                                             {}).get('nickname', None)
        current_first_name = msg.from_user.first_name
        await self.bot.send_message(msg.chat.id,
                                    get_response('nickname.ask_nickname',
                                            current_nickname=current_nickname,
                                            current_firstname=current_first_name),
                                            parse_mode='Markdown',
                                            reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def save_nickname(self, msg: Message):
        """Save the user's nickname after they provide it."""
        await self.user_manager.bind_user(msg.from_user.id)
        nickname = msg.text.strip()

        # Validate the nickname
        validator = AccountValidator()
        is_valid, validation_message = validator.validate_nickname(nickname)
        if is_valid:
            # Proceed to store the user data if the nickname is valid
            await self.user_manager.update_profile(**{"nickname": nickname})
            await self.user_manager.toggle_flag("awaiting_nickname", False)
            await self.bot.send_message(
                msg.chat.id,
                get_response('nickname.nickname_was_set', nickname=nickname),
                reply_markup=KeyboardMarkupGenerator().main_buttons(),
                parse_mode='HTML'
            )

        else:
            # Notify the user about the invalid nickname
            await self.bot.send_message(
                msg.chat.id,
                f"{validation_message}",
            )

    async def get_set_nickname_response(self, msg: Message):
        """return set nickname response"""
        await self.user_manager.bind_user(msg.chat.id)
        await self.user_manager.toggle_flag('awaiting_nickname', True)
        user_data = await self.user_manager.fetch_user()
        current_nickname = user_data.get('profile',{}).get('nickname', None)
        current_first_name = msg.chat.first_name
        return get_response('nickname.ask_nickname',
                            current_nickname=current_nickname,
                            current_firstname=current_first_name)

    @staticmethod
    def generate_random_nickname():
        """Generate a random nickname from a predefined list."""
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
