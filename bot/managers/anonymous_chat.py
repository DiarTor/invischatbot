from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import Message

from bot.utils.database import active_chats_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


def anonymous_chat(msg: Message, bot: TeleBot):
    user_chat = active_chats_collection.find_one({"user_id": msg.from_user.id})

    if user_chat and user_chat.get("replying"):
        # User is in reply mode
        recipient_id = user_chat['reply_target_user_id']
        original_message_id = user_chat['reply_target_message_id']

        # Send the reply text to the recipient in the context of their chat
        bot.send_message(
            recipient_id,
            f"پاسخ جدیدی از کاربر دریافت شد: {msg.text}",
            reply_to_message_id=original_message_id,
            parse_mode='Markdown'
        )

        # Notify the sender that their reply was sent
        bot.send_message(
            msg.chat.id,
            "پاسخ شما ارسال شد!",
            parse_mode='Markdown'
        )

        # Reset the replying state
        active_chats_collection.update_one(
            {"user_id": msg.from_user.id},
            {"$unset": {"replying": "", "reply_target_message_id": "", "reply_target_user_id": ""}}  # Clear reply state
        )
    else:
        active_chat = active_chats_collection.find_one(
            {"user_id": msg.from_user.id, "chats.open": True, 'replying': False},
            {"chats.$": 1}  # Only return the open chat
        )

        if active_chat and 'chats' in active_chat:
            recipient_id = active_chat['chats'][0]['target_user_id']
            try:
                # Forward the message to the recipient anonymously
                bot.send_message(
                    recipient_id,
                    get_response('recipient', msg.text),
                    reply_markup=KeyboardMarkupGenerator().recipient_buttons(msg.from_user.id, msg.id),
                    parse_mode='Markdown'
                )
            except ApiTelegramException:
                bot.send_message(msg.chat.id, get_response('errors.bot_blocked'))
                active_chats_collection.update_one(
                    {"user_id": msg.from_user.id, "chats.target_user_id": recipient_id, "chats.open": True},
                    {"$set": {"chats.$.open": False}}
                )
                return

            # Notify the sender that their message was successfully sent
            bot.send_message(msg.chat.id, get_response('sent'), parse_mode='Markdown')
            # Close the active chat
            active_chats_collection.update_one(
                {"user_id": msg.from_user.id, "chats.target_user_id": recipient_id, "chats.open": True},
                {"$set": {"chats.$.open": False}}
            )
        else:
            # Notify the sender that they are not currently in an anonymous chat
            bot.send_message(
                msg.chat.id,
                get_response('errors.no_active_chat'),
                parse_mode='Markdown'
            )
