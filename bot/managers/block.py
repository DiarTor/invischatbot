"""Handles user blocking functionalities in the bot."""
from datetime import datetime
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

        # Get current user's blocklist (dict of {user_id: {note, timestamp}})
        user_data = await self.user_manager.fetch_user()
        blocklist = user_data.get("chatting", {}).get("blocklist", {})

        if not blocklist:  # empty dict means no blocks
            await self.bot.send_message(
                chat_id=user_id,
                text=get_response("blocking.blocklist_empty")
            )
            return

        # Extract blocked user_ids (keys in the dict)
        blocked_user_ids = list(blocklist.keys())

        # Convert blocked user_ids → anon_ids
        blocklist_anon_ids = [anon_id async for anon_id in self.get_blocked_users_anon_ids()]

        # Get current user's anon_id
        user_anon_id = await self.user_manager.get_anon_id()

        # Send message with inline keyboard (start from first page)
        await self.bot.send_message(
            chat_id=user_id,
            text=get_response("blocking.blocklist"),
            parse_mode="Markdown",
            reply_markup=self.keyboard.blocklist_buttons(
                blocker_id=user_anon_id,
                blocked_list=blocklist_anon_ids,
                page=0  # 👈 start at first page
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
        await self.user_manager.update_fields({"$set":{f"chatting.blocklist.{blocked_user_id}": {
            "note": "",
            "timestamp": datetime.now().timestamp()
        }}})
        await self.bot.edit_message_reply_markup(blocker_id, callback.message.id,
                                                 reply_markup=self.keyboard.blocked_buttons(blocked_id,))

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
        """
        Unblock user
        :param blocker_id: Blocker anonymous ID
        :param blocked_id: Blocked anonymous ID
        :param callback: Callback Query
        """
        chat_id = callback.message.chat.id

        # Get numeric user_id of blocked user
        blocked_user_id = await get_user_id(blocked_id)
        if blocked_user_id is None:
            await self.bot.answer_callback_query(
                callback.id,
                "کاربر پیدا نشد.",  # User not found
                show_alert=True
            )
            return

        # Bind current user
        await self.user_manager.bind_user(chat_id)

        # Remove the key from the blocklist dict
        await self.user_manager.update_fields({
            "$unset": {f"chatting.blocklist.{blocked_user_id}": ""}
        })

        # Notify user
        await self.bot.answer_callback_query(
            callback.id,
            get_response("blocking.unblock_confirm", anon_id=blocked_id),
            show_alert=True
        )

        # Rebuild current blocklist
        blocklist = [anon_id async for anon_id in self.get_blocked_users_anon_ids()]

        if not blocklist:
            # No more blocked users → edit message
            await self.bot.edit_message_text(
                text=get_response("blocking.blocklist_empty"),
                chat_id=chat_id,
                message_id=callback.message.message_id
            )
            return

        # Update inline keyboard
        await self.bot.edit_message_reply_markup(
            chat_id,
            callback.message.message_id,
            reply_markup=self.keyboard.blocklist_buttons(blocker_id, blocklist)
        )


    async def cancel_unblock_user(self, blocker_anon_id: str, bot_message_id):
        """ Cancel unblock user operation """
        chat_id = await get_user_id(blocker_anon_id)
        await self.user_manager.bind_user(chat_id)
        blocked_users = [anon_id async for anon_id in self.get_blocked_users_anon_ids()]
        keyboard = self.keyboard.blocklist_buttons(blocker_anon_id, blocked_users)
        await self.bot.edit_message_reply_markup(chat_id,
                                                 bot_message_id,
                                                 reply_markup=keyboard)

    async def unblock_all_users(self, callback: CallbackQuery):
        """ Unblock all users """
        chat_id = callback.message.chat.id
        await self.user_manager.bind_user(chat_id)
        await self.user_manager.update_fields({"$unset": {"chatting.blocklist": {}}})
        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=callback.message.id,
            text=get_response("blocking.unblock_all_confirm"),
            parse_mode="HTML",
        )

    async def add_note_request(self, callback: CallbackQuery, blocked_id: str):
        """ Add note to blocked user
        :param callback: Callback query
        :param blocked_user_id: Blocked user ID
        """
        await self.user_manager.bind_user(callback.from_user.id)
        await self.user_manager.toggle_flag('awaiting_block_note', True)
        await self.user_manager.update_fields({'$set': {'chatting.block_note_for': blocked_id}})
        await self.user_manager.update_fields({'$set': {'chatting.callback_id': callback.message.id}})
        await self.bot.send_message(
            chat_id=callback.from_user.id,
            text=get_response('blocking.add_note'),
            parse_mode='HTML',
            reply_markup=self.keyboard.cancel_buttons()
        )

    async def save_block_note(self, msg: telebot.types.Message):
        """ Save note for blocked user
        :param msg: Message containing the note
        """
        await self.user_manager.bind_user(msg.from_user.id)
        await self.validate_note(msg)
        note = msg.text.strip()
        user_data = await self.user_manager.fetch_user()
        blocked_id = user_data.get('chatting', {}).get('block_note_for')
        blocked_user_id = await get_user_id(blocked_id)
        callback_id = user_data.get('chatting', {}).get('callback_id')
        await self.user_manager.update_fields({f'chatting.blocklist.{blocked_user_id}.note': note})
        await self.user_manager.toggle_flag('awaiting_block_note', False)
        await self.user_manager.update_fields({'$unset': {'chatting.block_note_for': ""}})
        await self.bot.edit_message_reply_markup(msg.from_user.id, callback_id,
                                                 reply_markup=self.keyboard.blocked_buttons(
                                                     sender_id=blocked_id,
                                                     note_added=True
                                                ))
        await self.user_manager.update_fields({'$unset': {'chatting.callback_id': ""}})

        await self.bot.send_message(
            msg.chat.id,
            get_response('blocking.note_saved'),
            parse_mode='HTML',
            reply_markup=KeyboardMarkupGenerator().main_buttons()
        )

    async def get_block_note(self, callback: CallbackQuery, blocked_id: str):
        """ Get note for blocked user
        :param callback: Callback query
        :param blocked_id: Blocked anonymous ID
        """
        await self.user_manager.bind_user(callback.from_user.id)
        blocked_user_id = await get_user_id(blocked_id)
        user_data = await self.user_manager.fetch_user()
        blocklist = user_data.get('chatting', {}).get('blocklist', {})
        note = blocklist.get(str(blocked_user_id), {}).get('note', '')
        if not note:
            return None
        return note

    from typing import AsyncGenerator

    async def get_blocked_users_anon_ids(self) -> AsyncGenerator[str, None]:
        """Lazily yield anon_ids (memory-efficient for large blocklists)."""
        user_data = await self.user_manager.fetch_user()
        blocklist = user_data.get("chatting", {}).get("blocklist", {})

        if not blocklist:
            return  # nothing to yield

        # Keys of the dict are the blocked user_ids (as strings)
        blocked_user_ids = [int(uid) for uid in blocklist.keys()]

        async for user in mongo.users_collection.find(
            {"user_id": {"$in": blocked_user_ids}},
            {"anon_id": 1}
        ):
            anon_id = user.get("anon_id")
            if anon_id:
                yield anon_id

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

    async def validate_note(self, msg: telebot.types.Message) -> bool:
        if not msg.text:
            await self.bot.send_message(
                msg.chat.id,
                get_response('blocking.note_not_text'),
                parse_mode='HTML',
            )
            return False
        if len(msg.text) > 200:
            await self.bot.send_message(
                msg.chat.id,
                get_response('blocking.note_too_long'),
                parse_mode='HTML',
            )
            return False
        return True
    @staticmethod
    async def is_user_blocked(sender_anon_id: str, recipient_id: int) -> bool:
        """
        Check if a user is blocked.
        :param sender_anon_id: Anonymous ID of sender.
        :param recipient_id: User ID of recipient.
        :return: True if either user has blocked the other, False otherwise.
        """
        sender_data = await find_one(mongo.users_collection, {"anon_id": sender_anon_id})
        recipient_data = await find_one(mongo.users_collection, {"user_id": recipient_id})

        if not sender_data or not recipient_data:
            return False  # If data is missing, assume not blocked

        sender_id = sender_data["user_id"]
        recipient_id_str = str(recipient_id)
        sender_id_str = str(sender_id)

        sender_blocklist = sender_data.get("chatting", {}).get("blocklist", {})
        recipient_blocklist = recipient_data.get("chatting", {}).get("blocklist", {})

        return (
            recipient_id_str in sender_blocklist
            or sender_id_str in recipient_blocklist
        )

