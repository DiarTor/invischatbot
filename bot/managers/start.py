import uuid
from datetime import datetime

from decouple import config
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.user_data import close_existing_chats
from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


class StartBot:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def start(self, msg: Message):
        try:
            user_id = msg.from_user.id
            target_user_id = self._get_target_user_id(msg)
            self._store_user_data(user_id, nickname=msg.from_user.first_name)

            # Retrieve user and target user info in a single query
            user_data = users_collection.find_one({"user_id": user_id})

            if target_user_id:
                target_user_data = users_collection.find_one({"id": target_user_id})
                if target_user_data:
                    await self._manage_chats(user_data, target_user_data)
                else:
                    await self.bot.send_message(user_id, get_response('errors.no_user_found'))
            else:
                # No target ID, close existing chats and reset replying state
                close_existing_chats(user_id)
                await self._send_welcome_message(msg)

        except (ValueError, IndexError):
            await self._send_error_message(msg, 'errors.wrong_id')

    async def link(self, msg: Message):
        user_bot_id = users_collection.find_one({"user_id": msg.from_user.id})['id']
        link = self._generate_link(user_bot_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('greeting.link', link),
            parse_mode='Markdown'
        )

    def _store_user_data(self, user_id: int, nickname: str = None):
        """Store user data in the database."""
        if not self._is_user_in_database(user_id):
            user_data = {
                "id": f"{str(uuid.uuid4())[:5]}{str(uuid.uuid4().int)[-5:]}",
                "user_id": user_id,
                "nickname": nickname,
                "awaiting_nickname": False,
                "joined_at": datetime.timestamp(datetime.now()),
                "chats": [],
                "blocklist": []
            }
            users_collection.insert_one(user_data)

    @staticmethod
    def _get_target_user_id(msg: Message):
        """Extract the target user ID from the message."""
        parts = msg.text.split()[1:]
        return str(parts[0]) if parts else None

    async def _manage_chats(self, user_data, target_user_data):
        user_id = user_data['user_id']
        target_user_id = target_user_data['user_id']

        # Close existing chats only if they are not with the target user
        if not any(chat['target_user_id'] == target_user_id and chat['open'] for chat in user_data.get('chats', [])):
            close_existing_chats(user_id)

        # Check if there's already an open chat with the target user
        if any(chat['target_user_id'] == target_user_id for chat in user_data.get('chats', [])):
            await self._reopen_chat(user_id, target_user_id, target_user_data['nickname'])
        else:
            await self._create_new_chat(user_id, target_user_id, target_user_data['nickname'])

    async def _reopen_chat(self, user_id: int, target_user_id: int, target_user_nickname: str):
        users_collection.update_one(
            {"user_id": user_id, "chats.target_user_id": target_user_id},
            {
                "$set": {
                    "chats.$.open": True,
                    "chats.$.chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            }
        )
        await self.bot.send_message(user_id, get_response('texting.sending.send', target_user_nickname),
                                    parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def _create_new_chat(self, user_id: int, target_user_id: int, target_user_nickname: str):
        target_user_bot_id = users_collection.find_one({"user_id": target_user_id})['id']
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "chats": {
                        "target_user_bot_id": target_user_bot_id,
                        "target_user_id": target_user_id,
                        "chat_created_at": datetime.timestamp(datetime.now()),
                        "chat_started_at": datetime.timestamp(datetime.now()),
                        "open": True
                    }
                }
            },
            upsert=True
        )
        await self.bot.send_message(user_id, get_response('texting.sending.send', target_user_nickname),
                                    parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def _send_welcome_message(self, msg: Message):
        """Send a welcome message to the user."""
        await self.bot.send_message(msg.chat.id, get_response('greeting.welcome', msg.from_user.first_name),
                                    parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().main_buttons())

    async def _send_error_message(self, msg: Message, error_key: str):
        """Send an error message to the user."""
        await self.bot.send_message(msg.chat.id, get_response(error_key), parse_mode='Markdown')

    @staticmethod
    def _is_user_in_database(user_id: int):
        """Check if the target user ID is in the database (Target user started the bot)."""
        return users_collection.find_one({'user_id': user_id})

    @staticmethod
    def _generate_link(user_id: int) -> str:
        """Generate a link to the bot for the user."""
        return f"https://t.me/{config('BOT_USERNAME', cast=str)}?start={user_id}"
