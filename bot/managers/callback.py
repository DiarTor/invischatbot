from telebot import TeleBot
from telebot.types import CallbackQuery

from bot.utils.database import active_chats_collection


def callback_manager(callback: CallbackQuery, bot: TeleBot):
    if callback.data.startswith('reply'):
        action, sender_id, message_id = callback.data.split('-')

        # Set the replying flag and store the original message ID temporarily
        active_chats_collection.update_one(
            {"user_id": callback.from_user.id},
            {
                "$set": {
                    "replying": True,
                    "reply_target_message_id": message_id,
                    "reply_target_user_id": int(sender_id),
                }
            }
        )

        # Ask the user to send their reply text
        bot.send_message(
            callback.from_user.id,
            "لطفاً متن پاسخ خود را ارسال کنید:",
            parse_mode='Markdown'
        )

    bot.answer_callback_query(callback.id)