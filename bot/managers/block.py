import telebot

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.chat_utils import get_seen_status, get_marked_status
from bot.common.database_utils import fetch_user_data_by_query, get_user_id


class BlockUserManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def block_list(self, msg: telebot.types.Message):
        """ Show user blocklist"""
        user_id = msg.chat.id
        blocklist = users_collection.find_one({'user_id': user_id}).get('blocklist', None)
        if not blocklist:
            await self.bot.send_message(text=get_response('blocking.blocklist_empty'), chat_id=user_id)
            return
        keyboard = KeyboardMarkupGenerator()
        user_anon_id = users_collection.find_one({'user_id': user_id}).get('id', None)
        await self.bot.send_message(chat_id=user_id, text=get_response("blocking.blocklist"), parse_mode='Markdown',
                                    reply_markup=keyboard.blocklist_buttons(user_anon_id, blocklist))

    async def block_user(self, blocker_id: int, blocked_id: str, callback: CallbackQuery):
        """ Block user
        :param blocker_id: Blocker ID
        :param blocked_id: Blocked anonymous ID
        :param callback: Callback query
        """
        blocklist = users_collection.find_one({'user_id': blocker_id}).get('blocklist', None)
        if blocked_id in blocklist:
            await self.bot.answer_callback_query(callback.id, get_response('blocking.already_blocked'))
            return
        users_collection.update_one(
            {"user_id": blocker_id},
            {"$addToSet": {"blocklist": blocked_id}}, upsert=True
        )
        await self.bot.edit_message_reply_markup(blocker_id, callback.message.id,
                                                 reply_markup=KeyboardMarkupGenerator().blocked_buttons())

    async def cancel_block(self, callback: CallbackQuery, reply_message_id, sender_id):
        """ Cancel blocking operation
        :param callback: Callback query
        :param reply_message_id: Reply message ID
        :param sender_id: Sender anonymous ID
        """
        chat_id = callback.message.chat.id
        seen = get_seen_status(user_id=chat_id, message_id=reply_message_id)
        marked = get_marked_status(callback.message.text)
        await self.bot.edit_message_reply_markup(callback.message.chat.id, callback.message.id,
                                                 reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_id,
                                                                                                          reply_message_id,
                                                                                                          seen, marked))

    async def unblock_user(self, blocker_id: str, blocked_id: str, callback: CallbackQuery):
        """ Unblock user
        :param blocker_id: Blocker anonymous ID
        :param blocked_id: Blocked anonymous ID
        :param callback: Callback Query
        """
        users_collection.update_one({'id': blocker_id}, {'$pull': {'blocklist': blocked_id}})
        chat_id = callback.message.chat.id
        await self.bot.answer_callback_query(callback.id, get_response('blocking.unblock_confirm', anon_id=blocked_id),
                                             show_alert=True)
        blocklist = users_collection.find_one({'user_id': chat_id}).get('blocklist', None)
        if not blocklist:
            await self.bot.edit_message_text(text=get_response('blocking.blocklist_empty'), chat_id=chat_id,
                                             message_id=callback.message.message_id)
            return
        user_anon_id = users_collection.find_one({'user_id': chat_id}).get('id', None)
        await self.bot.edit_message_reply_markup(chat_id, callback.message.message_id,
                                                 reply_markup=KeyboardMarkupGenerator().blocklist_buttons(user_anon_id,
                                                                                                          blocklist))

    async def cancel_unblock_user(self, blocker_anon_id, bot_message_id):
        blocker_data = users_collection.find_one({'id': str(blocker_anon_id)})
        blocklist = blocker_data.get('blocklist', None)
        chat_id = get_user_id(blocker_anon_id)
        await self.bot.edit_message_reply_markup(chat_id, bot_message_id,
                                                 reply_markup=KeyboardMarkupGenerator().blocklist_buttons(blocker_anon_id,
                                                                                                          blocklist))
    @staticmethod
    async def is_user_blocked(sender_id: str, recipient_id: int) -> bool:
        """
        Check if a user is blocked.
        :param sender_id: Anonymous ID of sender.
        :param recipient_id: User ID of recipient.
        :return: True if either user has blocked the other, False otherwise.
        """
        sender_data = fetch_user_data_by_query({"id": sender_id})
        recipient_data = fetch_user_data_by_query({"user_id": recipient_id})

        if not sender_data or not recipient_data:
            return False  # If data is missing, assume not blocked

        sender_blocklist = sender_data.get('blocklist', [])
        recipient_blocklist = recipient_data.get('blocklist', [])

        return sender_data['id'] in recipient_blocklist or recipient_data['id'] in sender_blocklist