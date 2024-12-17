import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.user_data import get_seen_status


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
        user_anny_id = users_collection.find_one({'user_id': user_id}).get('id', None)
        await self.bot.send_message(chat_id=user_id, text=get_response("blocking.blocklist"), parse_mode='Markdown',
                                    reply_markup=keyboard.blocklist_buttons(user_anny_id, blocklist))

    async def block_user(self, blocker_id: int, blocked_id: str, callback: CallbackQuery):
        """ Block user
        :param blocker_id: Blocker ID
        :param blocked_id: Blocked anny ID
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
        :param sender_id: Sender anny ID
        """
        chat_id = callback.message.chat.id
        seen = get_seen_status(user_id=chat_id, message_id=reply_message_id)
        await self.bot.edit_message_reply_markup(callback.message.chat.id, callback.message.id,
                                                 reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_id,
                                                                                                          reply_message_id,
                                                                                                          seen))

    async def unblock_user(self, blocker_id: str, blocked_id: str, callback: CallbackQuery):
        """ Unblock user
        :param blocker_id: Blocker anny ID
        :param blocked_id: Blocked anny ID
        :param callback: Callback Query
        """
        users_collection.update_one({'id': blocker_id}, {'$pull': {'blocklist': blocked_id}})
        chat_id = callback.message.chat.id
        await self.bot.answer_callback_query(callback.id, get_response('blocking.unblock_confirm', blocked_id),
                                             show_alert=True)
        blocklist = users_collection.find_one({'user_id': chat_id}).get('blocklist', None)
        if not blocklist:
            await self.bot.edit_message_text(text=get_response('blocking.blocklist_empty'), chat_id=chat_id,
                                             message_id=callback.message.message_id)
            return
        user_anny_id = users_collection.find_one({'user_id': chat_id}).get('id', None)
        await self.bot.edit_message_reply_markup(chat_id, callback.message.message_id,
                                                 reply_markup=KeyboardMarkupGenerator().blocklist_buttons(user_anny_id,
                                                                                                          blocklist))

    async def cancel_unblock_user(self, blocker_id, message_id, bot_message_id):
        user = users_collection.find_one({'id': str(blocker_id)})
        blocklist = user.get('blocklist', None)
        chat_id = user.get('user_id', None)
        await self.bot.edit_message_text(text=get_response('blocking.blocklist'), chat_id=chat_id,
                                         message_id=bot_message_id,
                                         reply_markup=KeyboardMarkupGenerator().blocklist_buttons(chat_id, blocklist,
                                                                                                  message_id),
                                         parse_mode='Markdown')
