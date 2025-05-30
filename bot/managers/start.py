import re
from datetime import datetime

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.admin.adminstration import Admin
from bot.common.chat_utils import close_chats
from bot.common.database_utils import is_user_banned, save_user_data, fetch_user_data_by_id, user_exists, update_user_fields, \
    get_user_anon_id
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.common.user import is_bot_status_off
from bot.database.database import users_collection
from bot.languages.response import get_response
from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager


class StartBot:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def start(self, msg: Message, default_target_anon_id=None):
        try:
            user_id = msg.chat.id
            nickname = msg.from_user.first_name
            target_anon_id = default_target_anon_id or await self._get_target_user_id(msg)

            # If the user doesn't exist in the database, store their data
            if not await user_exists(user_id):
                await save_user_data(user_id, nickname=nickname, username=msg.from_user.username or None,
                               first_name=msg.from_user.first_name or None, last_name=msg.from_user.last_name or None)
            if is_user_banned(user_id):
                await self.bot.send_message(user_id, get_response('account.ban.banned'))
                return

            # if not await is_subscribed_to_channel(self.bot, user_id):
            #     await self.bot.send_message(user_id, get_response('ad.force_join'),
            #                                 reply_markup=KeyboardMarkupGenerator().force_join_buttons())
            #     return
            # Retrieve user data from the database
            user_data = users_collection.find_one({"user_id": user_id})
            if not target_anon_id and user_data.get('first_time'):
                parts = msg.text.split()[1:]  # Get arguments after /start
                if parts and str(parts[0]).startswith('ref_'):  # Check if parts is not empty before accessing index 0
                    await AccountManager(self.bot).referral(msg)
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('greeting.first_time', nickname=nickname),
                    reply_markup=KeyboardMarkupGenerator().main_buttons(),  # Inline keyboard for first time
                    parse_mode='Markdown',
                )
                await Admin(self.bot).announce_new_user(user_id)
                # Update the user field to mark them as not first time
                await update_user_fields(user_id, 'first_time', False)
                return
            # If no target user provided, close any open chats and send a general welcome message
            if not target_anon_id:
                close_chats(user_id)
                await self._send_welcome_message(msg)
                return

            # If it's the user's first time, show a welcome message and explain the process
            if user_data.get('first_time'):
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('greeting.first_time', nickname=nickname),
                    reply_markup=KeyboardMarkupGenerator().main_buttons(),  # Inline keyboard for first time
                    parse_mode='Markdown',
                )
                await Admin(self.bot).announce_new_user(user_id)
                await update_user_fields(user_id, 'first_time', False)
            # Retrieve target user data
            target_user_data = users_collection.find_one({"id": target_anon_id})
            if not target_user_data:
                await self.bot.send_message(user_id, get_response('errors.no_user_found'))
                return

            # Check if the user is trying to message themselves
            if target_user_data["user_id"] == user_id:
                await self.bot.send_message(user_id, get_response('errors.cant_message_self'))

            # Check if the user is blocked by the target user
            if await BlockUserManager.is_user_blocked(user_data.get('id'), target_user_data["user_id"]):
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('blocking.blocked_by_user'),
                    reply_markup=KeyboardMarkupGenerator().main_buttons()
                )
                return

            # Check if the user's bot status is off
            if is_bot_status_off(user_id):
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('account.bot_status.self.off'),
                    reply_markup=KeyboardMarkupGenerator().main_buttons(),
                    parse_mode='Markdown'
                )
                return

            # Check if the target user's bot status is off
            if is_bot_status_off(target_user_data["user_id"]):
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('account.bot_status.recipient.off'),
                    reply_markup=KeyboardMarkupGenerator().main_buttons(),
                    parse_mode='Markdown'
                )
                return

            # Manage chats if all checks pass
            close_chats(user_id, True)
            await self._manage_chats(user_data, target_user_data)

        except (ValueError, IndexError) as e:
            print("Error in start method:", str(e))
            await self._send_error_message(msg, 'errors.wrong_id')

    @staticmethod
    async def _get_target_user_id(msg: Message):
        """Extract the target user ID from the message, allowing only English letters and numbers."""
        parts = msg.text.split()[1:]
        if not parts:
            return None
        if str(parts[0]).startswith('ref_'):
            return
        target_id = re.sub(r'[^a-zA-Z0-9]', '', parts[0])  # Remove non-alphanumeric characters
        return target_id if target_id else None

    async def _manage_chats(self, user_data, target_user_data):
        user_id = user_data['user_id']
        target_user_id = target_user_data['user_id']

        # Close existing chats only if they are not with the target user
        if not any(chat['target_user_id'] == target_user_id and chat['open'] for chat in user_data.get('chats', [])):
            close_chats(user_id)

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
        await self.bot.send_message(user_id, get_response('texting.sending.text.send', nickname=target_user_nickname),
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
        # create the chat for the target user with the sender information
        users_collection.update_one(
            {"user_id": target_user_id},
            {
                "$push": {
                    "chats": {
                        "target_user_anon_id": get_user_anon_id(user_id),
                        "target_user_id": user_id,
                        "chat_created_at": datetime.timestamp(datetime.now()),
                        "chat_started_at": datetime.timestamp(datetime.now()),
                        "open": False
                    }
                }
            },
            upsert=True
        )
        await self.bot.send_message(user_id, get_response('texting.sending.text.send', nickname=target_user_nickname),
                                    parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def _send_welcome_message(self, msg: Message):
        """Send a welcome message to the user."""
        nickname = fetch_user_data_by_id(msg.chat.id).get('nickname')
        await self.bot.send_message(msg.chat.id, get_response('greeting.welcome', nickname=nickname),
                                    reply_markup=KeyboardMarkupGenerator().main_buttons())

    async def _send_error_message(self, msg: Message, error_key: str):
        """Send an error message to the user."""
        await self.bot.send_message(msg.chat.id, get_response(error_key), parse_mode='Markdown')
