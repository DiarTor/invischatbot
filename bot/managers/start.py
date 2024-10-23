from decouple import config
from jdatetime import datetime
from telebot import TeleBot
from telebot.types import Message

from bot.utils.database import active_chats_collection
from bot.utils.language import get_response


def start(msg: Message, bot: TeleBot):
    try:
        if msg.text.split()[1:]:
            target_user_id = int(msg.text.split()[1])

            # Check for any existing open chats for the user
            existing_chat = active_chats_collection.find_one(
                {
                    "user_id": msg.from_user.id,
                    "chats.open": True
                }
            )

            # If there's an existing open chat, close it
            if existing_chat:
                # Close all open chats
                active_chats_collection.update_many(
                    {"user_id": msg.from_user.id, "chats.open": True},
                    {"$set": {"chats.$[].open": False}}  # Close all open chats
                )
                # Set replying to False for the user
                active_chats_collection.update_one(
                    {"user_id": msg.from_user.id},
                    {"$set": {"replying": False}}  # Set replying state to False
                )
            # Now we can create or reopen the chat with the new target user
            existing_chat_with_target = active_chats_collection.find_one(
                {
                    "user_id": msg.from_user.id,
                    "chats.target_user_id": target_user_id
                }
            )

            if existing_chat_with_target:
                # Reopen the existing chat if it was closed
                active_chats_collection.update_one(
                    {"user_id": msg.from_user.id, "chats.target_user_id": target_user_id},
                    {"$set": {
                        "chats.$.open": True,
                        "chats.$.chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "replying": False  # Set replying state to False
                    }}
                )
                bot.send_message(msg.chat.id, get_response('sending'), parse_mode='Markdown')
            else:
                # Create a new chat session since none exists
                active_chats_collection.update_one(
                    {"user_id": msg.from_user.id},
                    {
                        "$push": {
                            "chats": {
                                "target_user_id": target_user_id,
                                "chat_started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "open": True
                            }
                        },
                        "$set": {"replying": False}
                    },
                    upsert=True  # Insert if it doesn't exist, update otherwise
                )
                bot.send_message(msg.chat.id, get_response('sending'), parse_mode='Markdown')
        else:
            bot.send_message(msg.chat.id, get_response('welcome', msg.from_user.first_name), parse_mode='Markdown')
    except (ValueError, IndexError):
        bot.send_message(msg.chat.id, get_response('errors.wrong_id'), parse_mode='Markdown')


def link(msg: Message, bot: TeleBot):
    link = f"https://t.me/{config('BOT_USERNAME', cast=str)}?start={msg.from_user.id}"

    # Send the link to the user
    bot.send_message(
        msg.chat.id,
        get_response('link', link),
        parse_mode='Markdown'
    )
