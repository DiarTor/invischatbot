"""Handles user blocking functionalities in the bot."""
from typing import AsyncGenerator
import telebot

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.data import ChatDataManager, UserDataManager, get_user_id, find_one
from bot.database.database import mongo


class BlockUserManager:
    """Manager for handling user blocking functionalities."""
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.keyboard = KeyboardMarkupGenerator()
        self.chat_manager = ChatDataManager()
        self.user_manager = UserDataManager()

    async def block_list(self, msg: telebot.types.Message):
        """Show user blocklist using only anon_ids"""
        user_id = msg.chat.id
        await self.user_manager.bind_user(user_id=user_id)

        # Get current user's blocklist
        user_data = await self.user_manager.fetch_user()
        blocklist = user_data.get('chatting', {}).get('blocklist', [])

        if not blocklist:
            await self.bot.send_message(
                text=get_response('blocking.blocklist_empty'),
                chat_id=user_id
            )
            return
        blocklist_anon_ids = [anon_id async for anon_id in self.get_blocked_users_anon_ids()]
        user_anon_id = await self.user_manager.get_anon_id()
        await self.bot.send_message(
            chat_id=user_id,
            text=get_response("blocking.blocklist"),
            parse_mode='Markdown',
            reply_markup=self.keyboard.blocklist_buttons(
                blocker_id=user_anon_id,
                blocked_list=blocklist_anon_ids
            )
        )

    async def block_user(self, blocker_id: int, blocked_id: str, callback: CallbackQuery):
        """ Block user
        :param blocker_id: Blocker User ID
        :param blocked_id: Blocked anonymous ID
        :param callback: Callback query
        """
        await self.user_manager.bind_user(blocker_id)
        user = await self.user_manager.fetch_user()
        blocklist = user.get('chatting', {}).get('blocklist', [])
        blocked_user_id = await get_user_id(blocked_id)
        if blocked_user_id in blocklist:
            await self.bot.answer_callback_query(callback.id,
                                        get_response('blocking.already_blocked'))
            return

        await self.user_manager.update_fields({"$addToSet":{"chatting.blocklist": blocked_user_id}})
        await self.bot.edit_message_reply_markup(blocker_id, callback.message.id,
                                                 reply_markup=self.keyboard.blocked_buttons())

    async def cancel_block(self, callback: CallbackQuery, reply_message_id, sender_id):
        """ Cancel blocking operation
        :param callback: Callback query
        :param reply_message_id: Reply message ID
        :param sender_id: Sender anonymous ID
        """
        chat_id = callback.message.chat.id
        seen = await self.chat_manager.has_seen_message(user_id=chat_id,
                                                    message_id=callback.message.id)
        marked = self.chat_manager.is_text_marked(callback.message.text)
        await self.bot.edit_message_reply_markup(callback.message.chat.id,
                                                callback.message.id,
                                                reply_markup=self.keyboard.recipient_option_buttons(
                                                    sender_id,
                                                    reply_message_id,
                                                    seen,
                                                    marked))

    async def unblock_user(self, callback: CallbackQuery, blocker_id: str, blocked_id: str):
        """ Unblock user
        :param blocker_id: Blocker anonymous ID
        :param blocked_id: Blocked anonymous ID
        :param callback: Callback Query
        """
        chat_id = callback.message.chat.id
        blocked_user_id = await get_user_id(blocked_id)
        await self.user_manager.bind_user(chat_id)
        await self.user_manager.update_fields({'$pull': {'chatting.blocklist': blocked_user_id}})
        await self.bot.answer_callback_query(callback.id,
                                             get_response('blocking.unblock_confirm',
                                                          anon_id=blocked_id),
                                             show_alert=True)
        blocklist = [anon_id async for anon_id in self.get_blocked_users_anon_ids()]
        if not blocklist:
            await self.bot.edit_message_text(text=get_response('blocking.blocklist_empty'),
                                             chat_id=chat_id,
                                             message_id=callback.message.message_id)
            return
        await self.bot.edit_message_reply_markup(chat_id, callback.message.message_id,
                                            reply_markup=self.keyboard.blocklist_buttons(blocker_id,
                                                                                        blocklist))

    async def cancel_unblock_user(self, blocker_anon_id: str, bot_message_id):
        """ Cancel unblock user operation """
        chat_id = await get_user_id(blocker_anon_id)
        await self.user_manager.bind_user(chat_id)
        blocked_users = [anon_id async for anon_id in self.get_blocked_users_anon_ids()]
        keyboard = self.keyboard.blocklist_buttons(blocker_anon_id, blocked_users)
        await self.bot.edit_message_reply_markup(chat_id,
                                                 bot_message_id,
                                                 reply_markup=keyboard)

    async def get_blocked_users_anon_ids(self) -> AsyncGenerator[str, None]:
        """Lazily yield anon_ids (memory-efficient for large blocklists)."""
        user_data = await self.user_manager.fetch_user()
        blocklist = user_data.get('chatting', {}).get('blocklist', [])

        async for user in mongo.users_collection.find(
            {"user_id": {"$in": blocklist}},
            {"anon_id": 1}
        ):
            if user.get("anon_id"):
                yield user["anon_id"]

    async def validate_block_action(self, callback: CallbackQuery, blocked_anon_id: str) -> bool:
        """
        Validate if the block action can be performed.
        :param callback: Callback query
        :return: True if valid, False otherwise
        """
        blocker_user_id = callback.from_user.id
        blocked_user_id = await get_user_id(blocked_anon_id)
        if not blocked_user_id:
            await self.bot.answer_callback_query(callback.id,
                                                get_response('blocking.user_not_found'))
            return False
        if blocker_user_id == blocked_user_id:
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.self'))
            return False
        if await self.is_user_blocked(sender_anon_id=blocked_anon_id, recipient_id=blocker_user_id):
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.already_blocked'))
            return False
        if blocked_anon_id == 'support':
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.support'))
            return False
        return True

    @staticmethod
    async def is_user_blocked(sender_anon_id: str, recipient_id: int) -> bool:
        """
        Check if a user is blocked.
        :param sender_id: Anonymous ID of sender.
        :param recipient_id: User ID of recipient.
        :return: True if either user has blocked the other, False otherwise.
        """
        sender_data = await find_one(mongo.users_collection, {'anon_id': sender_anon_id})
        recipient_data = await find_one(mongo.users_collection, {'user_id': recipient_id})
        if not sender_data or not recipient_data:
            return False  # If data is missing, assume not blocked

        sender_blocklist = sender_data.get('chatting', []).get('blocklist', [])
        recipient_blocklist = recipient_data.get('chatting', []).get('blocklist', [])

        return sender_data['user_id'] in recipient_blocklist or recipient_data['user_id'] in sender_blocklist
