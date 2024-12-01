import uuid
from datetime import datetime

from decouple import config

from bot.utils.database import users_collection


def is_user_in_database(user_id: int):
    """
    Check if the user is in the database
    :param user_id: The user ID
    """
    return users_collection.find_one({'user_id': user_id})


def store_user_data(user_id: int, nickname: str = None):
    """
    Store the user data in the database.
    :param user_id: user ID.
    :param nickname: nickname of the user.

    id: the user anonymous ID that used inside the bot.
    user_id: the user ID (from telegram).
    nickname: the nickname of the user.
    awaiting_nickname: the user is entering their nickname status.
    joined_at: the timestamp the user started the bot.
    chats: the chats that the user started.
    blocklist: the users a user blocked.
    version: the version of the bot the user is currently running.
    """
    if not is_user_in_database(user_id):
        user_data = {
            "id": f"{str(uuid.uuid4())[:5]}{str(uuid.uuid4().int)[-5:]}",
            "user_id": user_id,
            "nickname": nickname,
            "awaiting_nickname": False,
            "joined_at": datetime.timestamp(datetime.now()),
            "chats": [],
            "blocklist": [],
            "version": config('VERSION', cast=float)
        }
        users_collection.insert_one(user_data)


def close_open_chats(user_id: int):
    """
    Close existing chats for the user.
    :param user_id: user id
    """
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"chats.$[].open": False}}  # Close all open chats
    )


def close_replying_chat(user_id: int):
    """
    Reset the replying state for the user.
    :param user_id: user id
    """
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"replying": False, "reply_target_message_id": "", "reply_target_user_id": ""}}
        # Clear reply state
    )


def close_all_chats(user_id: int):
    """
    close all chats for the user and reset replying state.
    :param user_id:
    """
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"replying": False, "reply_target_message_id": "", "reply_target_user_id": "",
                  "chats.$[].open": False}}  # Close all open chats, reset replying
    )


def get_user(user_id: int):
    """
    Retrieve user data from database
    :param user_id: user id
    """
    return users_collection.find_one({"user_id": user_id})


def is_user_blocked(sender_id: str, recipient_id: int) -> bool:
    """
    :param sender_id: anny id
    :param recipient_id: user id
    :return:
    """
    sender_data = users_collection.find_one({"id": sender_id})
    recipient_data = users_collection.find_one({"user_id": recipient_id})
    return recipient_data and (
            sender_data['id'] in recipient_data.get('blocklist', []) or
            recipient_data['id'] in sender_data.get('blocklist', [])
    )
