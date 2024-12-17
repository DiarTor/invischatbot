from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager
from bot.managers.nickname import NicknameManager
from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.user_data import get_user, update_user_field, get_user_id, close_open_chats, add_seen_message


class CallbackHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def handle_callback(self, callback: CallbackQuery):
        """Main method to handle callbacks from the user."""
        callback_data = callback.data
        if callback_data.startswith('reply'):
            await self._process_reply_callback(callback)
        elif callback_data.startswith('seen'):
            callback.data = callback_data.split('-')[1:]
            await self._process_seen_callback(callback)
        elif callback_data.startswith('block'):
            await self._process_block_callback(callback)
        elif callback_data.startswith('report'):
            await self._process_report_callback(callback)
        elif callback_data.startswith('unblock'):
            await self._process_unblock_callback(callback)
        elif callback_data.startswith('change-nickname'):
            await self._process_change_nickname(callback)
        elif callback_data.startswith('cancel'):
            await self._process_cancel(callback)
        await self.bot.answer_callback_query(callback.id)

    async def _process_reply_callback(self, callback: CallbackQuery):
        """Process the reply callback and set the replying state."""
        action, sender_id, message_id = callback.data.split('-')
        # Update the user's chat state to indicate they are replying
        close_open_chats(callback.from_user.id)
        self._set_replying_state(callback.from_user.id, message_id, sender_id)

        # Prompt the user to send their reply text
        await self.bot.send_message(
            callback.from_user.id,
            get_response('texting.replying.send'),
            reply_to_message_id=callback.message.id,
            parse_mode='Markdown',
            reply_markup=KeyboardMarkupGenerator().cancel_buttons()
        )

    async def _process_seen_callback(self, callback: CallbackQuery):
        """Process the seen callback"""
        sender_anny_id, message_id = callback.data
        sender_id = get_user_id(sender_anny_id)
        add_seen_message(callback.from_user.id, int(message_id)
                         )
        await self.bot.send_message(chat_id=sender_id, reply_to_message_id=message_id,
                                    text=get_response('texting.seen.recipient'))
        await self.bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.id,
                                                 reply_markup=KeyboardMarkupGenerator().recipient_buttons(
                                                     sender_anny_id, message_id, True))
        await self.bot.answer_callback_query(callback.id, get_response('texting.seen.sent'))

    async def _process_block_callback(self, callback: CallbackQuery):
        keyboard = KeyboardMarkupGenerator()
        if 'block' in callback.data.split('-'):
            action, sender_id, message_id = callback.data.split('-')
            if sender_id == get_user(callback.message.chat.id).get('id'):
                await self.bot.answer_callback_query(callback.id, get_response('blocking.self'))
                return
            if sender_id == 'support':
                await self.bot.answer_callback_query(callback.id, get_response('blocking.support'))
                return
            await self.bot.edit_message_reply_markup(callback.message.chat.id, callback.message.id,
                                                     callback.inline_message_id,
                                                     reply_markup=keyboard.block_confirmation_buttons(sender_id,
                                                                                                      message_id))
        elif 'block_confirm' in callback.data.split('-'):
            action, sender_id, message_id = callback.data.split('-')
            await BlockUserManager(self.bot).block_user(callback.message.chat.id, str(sender_id),
                                                        callback)
        elif 'block_cancel' in callback.data.split('-'):
            action, sender_id, message_id = callback.data.split('-')
            await BlockUserManager(self.bot).cancel_block(callback, message_id,
                                                          sender_id)

    async def _process_report_callback(self, callback: CallbackQuery):
        """Process the report callback"""
        await self.bot.answer_callback_query(callback.id, get_response('reporting.send'), show_alert=True)

    async def _process_unblock_callback(self, callback: CallbackQuery):
        keyboard = KeyboardMarkupGenerator()
        if 'unblock' in callback.data.split('-'):
            action, blocker_id, blocked_id, message_id = callback.data.split('-')
            await self.bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.id,
                                                     reply_markup=keyboard.unblock_confirmation_buttons(str(blocker_id),
                                                                                                        str(blocked_id),
                                                                                                        ))
        elif 'unblock_confirm' in callback.data.split('-'):
            action, blocker_id, blocked_id = callback.data.split('-')
            blocker_anny_id = users_collection.find_one({"user_id": callback.message.chat.id})['id']
            await BlockUserManager(self.bot).unblock_user(blocker_anny_id, str(blocked_id), callback)
        elif 'unblock_cancel' in callback.data.split('-'):
            action, blocker_id = callback.data.split('-')
            blocker_anny_id = users_collection.find_one({"user_id": callback.message.chat.id})['id']
            await BlockUserManager(self.bot).cancel_unblock_user(blocker_anny_id, str(blocker_id), callback.message.id)

    async def _process_change_nickname(self, callback: CallbackQuery):
        response = NicknameManager(self.bot).get_set_nickname_response(callback.message)
        await self.bot.edit_message_text(response, callback.message.chat.id, callback.message.id, parse_mode='Markdown',
                                         reply_markup=KeyboardMarkupGenerator().cancel_changing_nickname())

    async def _process_cancel(self, callback: CallbackQuery):
        action, task = callback.data.split('-')
        if task == "changing_nickname":
            update_user_field(callback.from_user.id, 'awaiting_nickname', False)
            await self.bot.edit_message_text(AccountManager(self.bot).get_account_response(callback.message),
                                             callback.from_user.id, callback.message.id, parse_mode='Markdown',
                                             reply_markup=KeyboardMarkupGenerator().account_buttons())

    @staticmethod
    def _set_replying_state(user_id: int, message_id: str, sender_id: str):
        """Set the replying state in the database."""
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "replying": True,
                    "reply_target_message_id": message_id,
                    "reply_target_user_id": str(sender_id),
                },
            }
        )
