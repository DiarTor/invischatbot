from datetime import datetime

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.user_data import close_existing_chats, is_user_blocked, store_user_data


class StartBot:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def start(self, msg: Message, default_target_anny_id=None):
        try:
            user_id = msg.from_user.id
            user_nickname = msg.from_user.first_name
            target_anny_id = default_target_anny_id or self._get_target_user_id(msg)

            store_user_data(user_id, nickname=user_nickname)
            user_data = users_collection.find_one({"user_id": user_id})

            # If no target user, close chats and send a welcome message
            if not target_anny_id:
                close_existing_chats(user_id)
                await self._send_welcome_message(msg)
                return

            # Retrieve target user data
            target_user_data = users_collection.find_one({"id": target_anny_id})
            if not target_user_data:
                await self.bot.send_message(user_id, get_response('errors.no_user_found'))
                return

            # Check invalid cases
            if target_user_data["user_id"] == user_id:
                await self.bot.send_message(user_id, get_response('errors.cant_message_self'))
                return

            if is_user_blocked(user_data.get('id'), target_user_data["user_id"]):
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('blocking.blocked_by_user'),
                    reply_markup=KeyboardMarkupGenerator().main_buttons()
                )
                return

            # Manage chats if all checks pass
            await self._manage_chats(user_data, target_user_data)

        except (ValueError, IndexError):
            await self._send_error_message(msg, 'errors.wrong_id')

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
        await self.bot.send_message(user_id, get_response('texting.sending.text.send', target_user_nickname),
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
        await self.bot.send_message(user_id, get_response('texting.sending.text.send', target_user_nickname),
                                    parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def _send_welcome_message(self, msg: Message):
        """Send a welcome message to the user."""
        await self.bot.send_message(msg.chat.id, get_response('greeting.welcome', msg.from_user.first_name),
                                    parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().main_buttons())

    async def _send_error_message(self, msg: Message, error_key: str):
        """Send an error message to the user."""
        await self.bot.send_message(msg.chat.id, get_response(error_key), parse_mode='Markdown')
