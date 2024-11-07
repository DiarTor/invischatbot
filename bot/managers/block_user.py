import telebot
from telebot.async_telebot import AsyncTeleBot

from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


class BlockUserManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def block_list(self, msg: telebot.types.Message):
        keyboard = KeyboardMarkupGenerator()
        blocklist = users_collection.find_one({'user_id': msg.from_user.id}).get('blocklist', None)
        user_bot_id = users_collection.find_one({'user_id': msg.from_user.id}).get('id', None)
        if not blocklist:
            await self.bot.send_message(text=get_response('blocking.blocklist_empty'), chat_id=msg.chat.id)
            return
        await self.bot.send_message(chat_id=msg.chat.id, text=get_response("blocking.blocklist"), parse_mode='Markdown',
                                    reply_markup=keyboard.blocklist_buttons(user_bot_id, blocklist, msg.id))

    async def block_user(self, blocker_id: int, blocked_id: int, bot_message_id):
        users_collection.update_one(
            {"user_id": blocker_id},
            {"$addToSet": {"blocklist": blocked_id}}, upsert=True
        )
        await self.bot.edit_message_text(
            text=get_response('blocking.block_confirm', blocked_id),
            chat_id=blocker_id,
            message_id=bot_message_id,
            parse_mode='Markdown',
        )

    async def cancel_block(self, chat_id, message_text, message_id, sender_id, bot_message_id: int):
        await self.bot.edit_message_text(text=get_response('texting.sending.recipient', message_text, sender_id), chat_id=chat_id,
                                   message_id=bot_message_id,
                                   reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_id, message_id,
                                                                                            message_text),
                                   parse_mode='Markdown')

    async def unblock_user(self, blocker_id, blocked_id, bot_message_id):
        users_collection.update_one({'id': int(blocker_id)}, {'$pull': {'blocklist': int(blocked_id)}})
        chat_id = users_collection.find_one({'id': int(blocker_id)}).get('user_id', None)
        await self.bot.edit_message_text(text=get_response('blocking.unblock_confirm', blocked_id), chat_id=chat_id,
                                   message_id=bot_message_id,
                                   parse_mode='Markdown')

    async def cancel_unblock_user(self, blocker_id, message_id, bot_message_id):
        user = users_collection.find_one({'id': int(blocker_id)})
        blocklist = user.get('blocklist', None)
        chat_id = user.get('user_id', None)
        await self.bot.edit_message_text(text=get_response('blocking.blocklist'), chat_id=chat_id,
                                   message_id=bot_message_id,
                                   reply_markup=KeyboardMarkupGenerator().blocklist_buttons(chat_id, blocklist,
                                                                                            message_id),
                                   parse_mode='Markdown')
