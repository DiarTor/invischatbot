import uuid

from decouple import config
from jdatetime import datetime
from telebot import TeleBot
from telebot.types import Message

from bot.managers.anonymous_chat import ChatHandler
from bot.utils.database import users_collection
from bot.utils.language import get_response


class StartBot:
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def start(self, msg: Message):
        try:
            user_id = msg.from_user.id
            target_user_id = self._get_target_user_id(msg)
            self._store_user_data(user_id, nickname=msg.from_user.first_name)

            # Retrieve user and target user info in a single query
            user_data = users_collection.find_one({"user_id": user_id})

            if target_user_id:
                target_user_data = users_collection.find_one({"user_id": target_user_id})
                if target_user_data:
                    self._manage_chats(msg, user_data, target_user_data)
                else:
                    self.bot.send_message(user_id, get_response('errors.no_user_found'))
            else:
                # No target ID, close existing chats and reset replying state
                self._close_existing_chats(user_id)
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
            "id": uuid.uuid4().int >> 99,
            "user_id": user_id,
            "nickname": nickname,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chats": [],
            "blocklist": []
        }
        if not self._is_user_in_database(user_id):
            users_collection.insert_one(user_data)

    @staticmethod
    def _get_target_user_id(msg: Message):
        """Extract the target user ID from the message."""
        parts = msg.text.split()[1:]
        return int(parts[0]) if parts else None

    def _manage_chats(self, msg: Message, user_data, target_user_data):
        user_id = user_data['user_id']
        target_user_id = target_user_data['user_id']

        # Close existing chats only if they are not with the target user
        if not any(chat['target_user_id'] == target_user_id and chat['open'] for chat in user_data.get('chats', [])):
            self._close_existing_chats(user_id)

        # Check if there's already an open chat with the target user
        if any(chat['target_user_id'] == target_user_id for chat in user_data.get('chats', [])):
            self._reopen_chat(user_id, target_user_id, target_user_data['nickname'])
        else:
            self._create_new_chat(user_id, target_user_id, target_user_data['nickname'])

    @staticmethod
    def _close_existing_chats(user_id: int):
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"replying": False, "reply_target_message_id": "", "reply_target_user_id": "",
                      "chats.$[].open": False}}  # Close all open chats, reset replying
        )

    def _reopen_chat(self, user_id: int, target_user_id: int, target_user_nickname: str):
        users_collection.update_one(
            {"user_id": user_id, "chats.target_user_id": target_user_id},
            {
                "$set": {
                    "chats.$.open": True,
                    "chats.$.chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            }
        )
        self.bot.send_message(user_id, get_response('texting.sending.send', target_user_nickname),
                              parse_mode='Markdown')

    def _create_new_chat(self, user_id: int, target_user_id: int, target_user_nickname: str):
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "chats": {
                        "target_user_id": target_user_id,
                        "chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "open": True
                    }
                }
            },
            upsert=True
        )
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
