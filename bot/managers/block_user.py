import telebot

from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


class BlockUserManager:
    def __init__(self, bot):
        self.bot = bot

    def block_list(self, msg: telebot.types.Message):
        keyboard = KeyboardMarkupGenerator()
        blocklist = users_collection.find_one({'user_id': msg.from_user.id}).get('blocklist', None)
        if not blocklist:
            self.bot.send_message(text=get_response('blocking.blocklist_empty'), chat_id=msg.chat.id)
            return
        self.bot.send_message(chat_id=msg.chat.id, text=get_response("blocking.blocklist"), parse_mode='Markdown',
                              reply_markup=keyboard.blocklist_buttons(msg.from_user.id, blocklist, msg.id))

    def block_user(self, blocker_id: int, blocked_id: int, bot_message_id):
        blocked_id = users_collection.find_one({'user_id': blocked_id}).get('id', None)
        users_collection.update_one(
            {"user_id": blocker_id},
            {"$addToSet": {"blocklist": blocked_id}}, upsert=True
        )
        self.bot.edit_message_text(
            text=get_response('blocking.block_confirm', blocked_id),
            chat_id=blocker_id,
            message_id=bot_message_id,
            parse_mode='Markdown',
        )

    def cancel_block(self, chat_id, message_text, message_id, sender_id, bot_message_id: int):
        self.bot.edit_message_text(text=get_response('texting.sending.recipient', message_text), chat_id=chat_id,
                                   message_id=bot_message_id,
                                   reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_id, message_id,
                                                                                            message_text),
                                   parse_mode='Markdown')

    def unblock_user(self, blocker_id, blocked_id, bot_message_id):
        users_collection.update_one({'user_id': int(blocker_id)}, {'$pull': {'blocklist': int(blocked_id)}})
        self.bot.edit_message_text(text=get_response('blocking.unblock_confirm', blocked_id), chat_id=blocker_id,
                                   message_id=bot_message_id,
                                   parse_mode='Markdown')

    def cancel_unblock_user(self, blocker_id, blocked_id, message_id, bot_message_id):
        blocklist = users_collection.find_one({'user_id': blocker_id}).get('blocklist', None)
        self.bot.edit_message_text(text=get_response('blocking.blocklist'), chat_id=blocker_id,
                                   message_id=bot_message_id,
                                   reply_markup=KeyboardMarkupGenerator().blocklist_buttons(blocker_id, blocklist,
                                                                                            message_id),
                                   parse_mode='Markdown')
