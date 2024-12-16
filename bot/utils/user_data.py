import uuid
from datetime import datetime

from decouple import config

from bot.utils.database import users_collection


def is_user_in_database(user_id: int):
    """
    Check if the user ID is in the database
    :param user_id: The user ID
    """
    return users_collection.find_one({'user_id': user_id})


def store_user_data(user_id: int, nickname: str = None):
    """
    Store user data in the database.
    :param user_id: user ID.
    :param nickname: nickname of the user."""
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


def close_existing_chats(user_id: int):
    """
    Close existing chats and replying state for the user.
    :param user_id: user id
    :return:
    """
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"replying": False, "reply_target_message_id": "", "reply_target_user_id": "",
                  "chats.$[].open": False}}  # Close all open chats, reset replying
    )


def reset_replying_state(user_id: int):
    """
    Reset the replying state for the user.
    :param user_id: user id
    """
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"replying": False, "reply_target_message_id": "", "reply_target_user_id": ""}}
        # Clear reply state
    )


def get_user(user_id: int):
    """
    Retrieve user data from database
    :param user_id: user id
    """
    return users_collection.find_one({"user_id": user_id})


def get_user_id(user_anny_id: str):
    """
    Retrieve user id from database
    :param user_anny_id: the user anonymous id
    :return: the user id
    """
    return users_collection.find_one({"id": user_anny_id}).get('user_id', None)


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


def update_user_field(user_id, field, value):
    """
    Update user field with new value
    :param user_id: user id
    :param field: the field you want to update
    :param value: new value of the field
    """
    users_collection.update_one({"user_id": user_id}, {"$set": {field: value}})


def close_open_chats(user_id: int):
    """
    Close existing chats for the user.
    :param user_id: user id
    """
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"chats.$[].open": False}}  # Close all open chats
    )


def add_seen_message(user_id, target_user_id, message_id):
    """
    Adds a message ID to the seen_messages array for a specific target user in the chats array.
    :param user_id: The ID of the user
    :param target_user_id: The ID of the target user in the chat
    :param message_id: The ID of the message to mark as seen
    """
    users_collection.update_one(
        {
            "user_id": user_id,
            "chats.target_user_id": target_user_id
        },
        {
            "$addToSet": {
                "chats.$.seen_messages": int(message_id)
            }
        }
    )


def get_seen_status(user_id, target_chat_id, message_id: int):
    """ Retrieve the seen status for the message from the database
    :param user_id: User ID of requester
    :param target_chat_id: Chat ID with the target user
    :param message_id: Message ID to check the seen status
    :return: Boolean indicating whether the message has been seen
    """
    # Query the database to get the 'seen_messages' for the specific chat
    user_data = users_collection.find_one(
        {"user_id": user_id, "chats.target_user_id": target_chat_id}
    )
    # Check if the 'seen_messages' array contains the given message_id
    if user_data:
        for chat in user_data['chats']:
            if chat['target_user_id'] == target_chat_id:
                return message_id in chat.get('seen_messages', [])

    # If no data is found, assume the message has not been seen
    return False
