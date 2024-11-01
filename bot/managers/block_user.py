from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


class BlockUserManager:
    def __init__(self, bot):
        self.bot = bot

    def block_user(self, blocker_id: int, blocked_id: int, bot_message_id):
        users_collection.update_one(
            {"user_id": blocker_id},
            {"$addToSet": {"blocked_users": blocked_id}}, upsert=True  # Add blocked_id to blocked_users list
        )
        self.bot.edit_message_text(
            text=get_response('blocking.block_confirm'),
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
