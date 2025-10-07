"""
StartBot class is responsible for managing the bot's behavior when a user starts the bot. 
It handles user registration, chat management, and various checks to ensure proper functionality.
"""
import re

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.admin.adminstration import Admin
from bot.common.data import ChatDataManager, UserDataManager, BotDataManager, find_one
from bot.database.database import mongo
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
# from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager


class StartBot:
    """
    StartBot is a class responsible for managing the start functionality of the bot,
    including user initialization, chat management, and handling various user states.
    """
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.user_manager = UserDataManager()
        self.chat_manager = ChatDataManager()
        self.bot_manager = BotDataManager()

    async def start(self, msg: Message, default_target_anon_id: str=None) -> None:
        """
        Handles the start command for the bot, initializing user data,
        managing chats, and sending appropriate responses.
        Args:
            msg (Message): The message object containing details about the user and the command.
            default_target_anon_id: The anonymous ID of the target user, if provided.
        """
        try:
            user_id = msg.chat.id
            await self.user_manager.bind_user(user_id)
            nickname = msg.from_user.first_name
            target_anon_id = default_target_anon_id or await self._get_target_user_id(msg)

            # If the user doesn't exist in the database, store their data
            if await self.user_manager.exists() is not True:
                username = msg.from_user.username.lower() if msg.from_user.username else None
                profile_data = {
                    "nickname": nickname,
                    "username": username,
                    "first_name": msg.from_user.first_name or '',
                    "last_name": msg.from_user.last_name or '',
                }
                await self.user_manager.save_user(**profile_data)
                await self.user_manager.update_last_interaction()
            if await self.user_manager.is_banned() is True:
                await self.bot.send_message(user_id, get_response('account.ban.banned'))
                return

            # save the last interaction time
            await self.user_manager.update_last_interaction()

            # Retrieve user data from the database
            user_data = await self.user_manager.fetch_user()
            user_version = user_data.get('metadata', {}).get('version', 1.0)
            bot_version = await self.bot_manager.get_bot_version()
            if user_version != bot_version:
                await self.user_manager.update_metadata(**{'version': bot_version})
    
            if not target_anon_id and await self.user_manager.get_flag_state('first_time') is False:
                await self.chat_manager.close_chats(user_id)
                await self._send_welcome_message(msg)
                return

            if await self.user_manager.get_flag_state('first_time') is True:
                if not target_anon_id:
                    await self.bot.send_message(
                    msg.chat.id,
                    get_response('greeting.first_time', nickname=nickname),
                    reply_markup=KeyboardMarkupGenerator().main_buttons(),
                    parse_mode='HTML',
                    )
                    await Admin(self.bot).announce_new_user(user_id)

                    # Update the user field to mark them as not first time
                    await self.user_manager.toggle_flag('first_time', False)
                    return
                else:
                    await self.bot.send_message(
                        msg.chat.id,
                        get_response('greeting.first_time', nickname=nickname),
                        reply_markup=KeyboardMarkupGenerator().main_buttons(),
                        parse_mode='HTML',
                    )
                    await Admin(self.bot).announce_new_user(user_id)
                    await self.user_manager.toggle_flag('first_time', False)

            # Check if the user's bot status is off
            if await self.user_manager.is_bot_disabled():
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('account.bot_status.self.off'),
                    reply_markup=KeyboardMarkupGenerator().main_buttons(),
                    parse_mode='Markdown'
                )
                return

            # Retrieve target user data
            target_user_data = await find_one(mongo.users_collection, {'anon_id': target_anon_id})
            if not target_user_data:
                await self.bot.send_message(user_id, get_response('errors.no_user_found'))
                return

            # Check if the user is trying to message themselves
            if target_user_data["user_id"] == user_id:
                await self.bot.send_message(user_id, get_response('errors.cant_message_self'))

            # Check if the user is blocked by the target user
            if await BlockUserManager.is_user_blocked(user_data.get('anon_id'),
                                                target_user_data["user_id"]):
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('blocking.blocked_by_user'),
                    reply_markup=KeyboardMarkupGenerator().main_buttons()
                )
                return



            # Check if the target user's bot status is off
            if target_user_data.get('flags', {}).get('is_bot_off', None):
                await self.bot.send_message(
                    msg.chat.id,
                    get_response('account.bot_status.recipient.off'),
                    reply_markup=KeyboardMarkupGenerator().main_buttons(),
                    parse_mode='Markdown'
                )
                return
            # Manage chats if all checks pass
            await self.user_manager.close_metadata()
            await self._manage_chats(user_data, target_user_data)

        except (ValueError, IndexError) as e:
            print(f"Error in start method: {str(e)}")
            await self._send_error_message(msg, 'errors.wrong_id')

    async def _manage_chats(self, user_data, target_user_data):
        user_id = user_data['user_id']
        target_user_id = target_user_data['user_id']

        # Close existing chats only if they are not with the target user
        is_chat_open = any(
            chat['target_user_id'] == target_user_id and chat['open']
            for chat in user_data.get('chatting', []).get('chats', [])
        )
        if not is_chat_open:
            await self.chat_manager.close_chats(user_id)

        # Bind the target user for further chat opening
        await self.user_manager.bind_user(target_user_id)

        # Check if there's already an open chat with the target user
        has_existing_chat = any(
            chat['target_user_id'] == target_user_id
            for chat in user_data.get('chatting', []).get('chats', [])
        )
        if has_existing_chat:
            nickname = target_user_data.get('profile', {}).get('nickname', 'N/A')
            bio = target_user_data.get('profile', {}).get('bio', 'درحال حاضر طرف بیوگرافی ندارد!')
            await self._reopen_chat(user_id, target_user_id, nickname, bio)
        else:
            nickname = target_user_data.get('profile', {}).get('nickname', 'N/A')
            bio = target_user_data.get('profile', {}).get('bio', 'درحال حاضر طرف بیوگرافی ندارد!')
            await self._create_new_chat(user_id, target_user_id, nickname, bio)

    async def _reopen_chat(self, user_id: int, target_user_id: int, target_user_nickname: str, bio: str):
        await self.chat_manager.reopen_chat(user_id, target_user_id)

        if await self.user_manager.get_anon_id() == 'support':
            response = 'texting.sending.support'
        else:
            response = 'texting.sending.text.send'
        await self.bot.send_message(user_id, get_response(response, nickname=target_user_nickname, bio=bio),
                                    parse_mode='HTML',
                                    reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def _create_new_chat(self, user_id: int, target_user_id: int, target_user_nickname: str, bio: str):
        target_user_anon_id = await self.user_manager.get_anon_id()
        # Create a single chat instance for the user
        if user_id == target_user_id:
            await self.chat_manager.create_chat(user_id, target_user_id, target_user_anon_id)
            await self.bot.send_message(user_id, get_response('texting.sending.text.send',
                                            nickname=target_user_nickname, bio=bio),
                                            parse_mode='HTML',
                                            reply_markup=KeyboardMarkupGenerator().cancel_buttons())
            return
        # create a chat instance for the sender.
        await self.chat_manager.create_chat(user_id, target_user_id, target_user_anon_id)

        # create the chat for the target user with the sender information
        await self.user_manager.bind_user(user_id)
        user_anon_id = await self.user_manager.get_anon_id()
        await self.chat_manager.create_chat(target_user_id, user_id, user_anon_id, open_chat=False)

        if target_user_anon_id == 'support':
            response = 'texting.sending.support'
        else:
            response = 'texting.sending.text.send'
        
        await self.bot.send_message(user_id, get_response(response, nickname=target_user_nickname, bio=bio),
                                    parse_mode='HTML',
                                    reply_markup=KeyboardMarkupGenerator().cancel_buttons())

    async def _send_welcome_message(self, msg: Message):
        """Send a welcome message to the user."""
        first_name = msg.from_user.first_name
        await self.bot.send_message(msg.chat.id, get_response('greeting.welcome',
                                                              first_name=first_name),
                                    reply_markup=KeyboardMarkupGenerator().main_buttons(),
                                    parse_mode='HTML', disable_web_page_preview=True)

    async def _send_error_message(self, msg: Message, error_key: str):
        """Send an error message to the user."""
        await self.bot.send_message(msg.chat.id, get_response(error_key), parse_mode='Markdown')

    @staticmethod
    async def _get_target_user_id(msg: Message):
        """Extract the target user ID from the message, allowing only English letters and numbers"""
        parts = msg.text.split()[1:]
        if not parts:
            return None
        if str(parts[0]).startswith('ref_'):
            return
        target_id = re.sub(r'[^a-zA-Z0-9]', '', parts[0])  # Remove non-alphanumeric characters
        return target_id if target_id else None
