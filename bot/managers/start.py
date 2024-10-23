from decouple import config
from jdatetime import datetime
from telebot import TeleBot
from telebot.types import Message

from bot.utils.database import active_chats_collection
from bot.utils.language import get_response


class StartBot:
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def start(self, msg: Message):
        try:
            target_user_id = self._get_target_user_id(msg)
            if target_user_id is not None:
                self._manage_chats(msg, target_user_id)
            else:
                self._send_welcome_message(msg)

        except (ValueError, IndexError):
            self._send_error_message(msg, 'errors.wrong_id')

    def link(self, msg: Message):
        link = self._generate_link(msg.from_user.id)
        self.bot.send_message(
            msg.chat.id,
            get_response('greeting.link', link),
            parse_mode='Markdown'
        )

    def _get_target_user_id(self, msg: Message):
        """Extract the target user ID from the message."""
        parts = msg.text.split()[1:]
        return int(parts[0]) if parts else None

    def _manage_chats(self, msg: Message, target_user_id: int):
        """Manage chat sessions for the user."""
        user_id = msg.from_user.id

        # Close existing open chats
        self._close_existing_chats(user_id)

        # Check if a chat with the target user already exists
        existing_chat_with_target = active_chats_collection.find_one(
            {
                "user_id": user_id,
                "chats.target_user_id": target_user_id
            }
        )

        if existing_chat_with_target:
            self._reopen_chat(user_id, target_user_id)
        else:
            self._create_new_chat(user_id, target_user_id)

    def _close_existing_chats(self, user_id: int):
        """Close all open chats for the user."""
        active_chats_collection.update_many(
            {"user_id": user_id, "chats.open": True},
            {"$set": {"chats.$[].open": False}}  # Close all open chats
        )
        # Set replying to False for the user
        active_chats_collection.update_one(
            {"user_id": user_id},
            {"$set": {"replying": False}}  # Set replying state to False
        )

    def _reopen_chat(self, user_id: int, target_user_id: int):
        """Reopen an existing chat with the target user."""
        active_chats_collection.update_one(
            {"user_id": user_id, "chats.target_user_id": target_user_id},
            {
                "$set": {
                    "chats.$.open": True,
                    "chats.$.chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "replying": False  # Set replying state to False
                }
            }
        )
        self.bot.send_message(user_id, get_response('texting.sending.send'), parse_mode='Markdown')

    def _create_new_chat(self, user_id: int, target_user_id: int):
        """Create a new chat session with the target user."""
        active_chats_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "chats": {
                        "target_user_id": target_user_id,
                        "chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "open": True
                    }
                },
                "$set": {"replying": False}  # Set replying state to False
            },
            upsert=True  # Insert if it doesn't exist, update otherwise
        )
        self.bot.send_message(user_id, get_response('texting.sending.send'), parse_mode='Markdown')

    def _send_welcome_message(self, msg: Message):
        """Send a welcome message to the user."""
        self.bot.send_message(msg.chat.id, get_response('greeting.welcome', msg.from_user.first_name), parse_mode='Markdown')

    def _send_error_message(self, msg: Message, error_key: str):
        """Send an error message to the user."""
        self.bot.send_message(msg.chat.id, get_response(error_key), parse_mode='Markdown')

    def _generate_link(self, user_id: int) -> str:
        """Generate a link to the bot for the user."""
        return f"https://t.me/{config('BOT_USERNAME', cast=str)}?start={user_id}"
