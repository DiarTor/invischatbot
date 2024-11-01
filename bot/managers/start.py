import uuid

from decouple import config
from jdatetime import datetime
from telebot import TeleBot
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.language import get_response


class StartBot:
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def start(self, msg: Message):
        try:
            target_user_id = self._get_target_user_id(msg)
            user_id = msg.from_user.id
            self._store_user_data(user_id, nickname=msg.from_user.first_name)
            # If the user provided a chat (target_user_id), manage the chat session
            if target_user_id is not None:
                if self._is_user_in_database(target_user_id):
                    self._manage_chats(msg, target_user_id)
                else:
                    self.bot.send_message(user_id, get_response('errors.no_user_found'))
            else:
                # No chat provided, just store user info and send welcome message
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

    def _store_user_data(self, user_id: int, nickname: str = None):
        """Store user data in the database."""
        user_data = {
            "id": uuid.uuid4().int >> 100,
            "user_id": user_id,
            "nickname": nickname,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if not self._is_user_in_database(user_id):
            users_collection.insert_one(user_data)

    @staticmethod
    def _get_target_user_id(msg: Message):
        """Extract the target user ID from the message."""
        parts = msg.text.split()[1:]
        return int(parts[0]) if parts else None

    def _manage_chats(self, msg: Message, target_user_id: int):
        """Manage chat sessions for the user."""
        user_id = msg.from_user.id

        # Close existing open chats
        self._close_existing_chats(user_id)

        # Check if a chat with the target user already exists
        existing_chat_with_target = users_collection.find_one(
            {
                "user_id": user_id,
                "chats.target_user_id": target_user_id
            }
        )

        if existing_chat_with_target:
            self._reopen_chat(user_id, target_user_id)
        else:
            self._create_new_chat(user_id, target_user_id)

    @staticmethod
    def _close_existing_chats(user_id: int):
        """Close all open chats for the user."""
        users_collection.update_many(
            {"user_id": user_id, "chats.open": True},
            {"$set": {"chats.$[].open": False}}  # Close all open chats
        )
        # Set replying to False for the user
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"replying": False}}  # Set replying state to False
        )

    def _reopen_chat(self, user_id: int, target_user_id: int):
        """Reopen an existing chat with the target user."""
        users_collection.update_one(
            {"user_id": user_id, "chats.target_user_id": target_user_id},
            {
                "$set": {
                    "chats.$.open": True,
                    "chats.$.chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "replying": False  # Set replying state to False
                }
            }
        )
        target_user_nickname = users_collection.find_one({'user_id': target_user_id})['nickname']
        self.bot.send_message(user_id, get_response('texting.sending.send', target_user_nickname),
                              parse_mode='Markdown')

    def _create_new_chat(self, user_id: int, target_user_id: int):
        """Create a new chat session with the target user."""
        users_collection.update_one(
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

        target_user_nickname = users_collection.find_one({'user_id': target_user_id})['nickname']
        self.bot.send_message(user_id, get_response('texting.sending.send', target_user_nickname),
                              parse_mode='Markdown')

    def _send_welcome_message(self, msg: Message):
        """Send a welcome message to the user."""
        self.bot.send_message(msg.chat.id, get_response('greeting.welcome', msg.from_user.first_name),
                              parse_mode='Markdown')

    def _send_error_message(self, msg: Message, error_key: str):
        """Send an error message to the user."""
        self.bot.send_message(msg.chat.id, get_response(error_key), parse_mode='Markdown')

    @staticmethod
    def _is_user_in_database(user_id: int):
        """Check if the target user ID is in the database (Target user started the bot)."""
        return users_collection.find_one({'user_id': user_id})

    @staticmethod
    def _generate_link(user_id: int) -> str:
        """Generate a link to the bot for the user."""
        return f"https://t.me/{config('BOT_USERNAME', cast=str)}?start={user_id}"
