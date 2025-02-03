import uuid
from datetime import datetime
from urllib.parse import quote

from decouple import config

from bot.utils.database import users_collection


def user_exists(user_id: int) -> bool:
    """
    Check if the user exists in the database.
    :param user_id: User ID to check.
    :return: True if user exists, False otherwise.
    """
    return bool(users_collection.find_one({'user_id': user_id}))


def create_unique_id() -> str:
    """Generate a unique 10-character ID."""
    return f"{str(uuid.uuid4())[:5]}{str(uuid.uuid4().int)[-5:]}"


def save_user_data(user_id: int, nickname: str = None) -> None:
    """
    Store user data in the database.
    :param user_id: User ID.
    :param nickname: Nickname of the user.
    """
    try:
        user_data = {
            "id": create_unique_id(),
            "user_id": user_id,
            "nickname": nickname,
            "awaiting_nickname": False,
            "joined_at": datetime.timestamp(datetime.now()),
            "chats": [],
            "blocklist": [],
            "is_bot_off": False,
            "version": config('VERSION', cast=float),
            "first_time": True
        }
        users_collection.insert_one(user_data)
    except Exception as e:
        print(f"Failed to store user data: {e}")


def get_user_by_id(user_id: int) -> dict | None:
    """
    Retrieve user data from the database.
    :param user_id: User ID.
    :return: User data dictionary or None if not found.
    """
    return users_collection.find_one({"user_id": user_id}) or None


def fetch_user_id(user_anny_id: str):
    """
    Retrieve user id from database
    :param user_anny_id: the user anonymous id
    :return: the user id
    """
    return users_collection.find_one({"id": user_anny_id}).get('user_id', None)


def get_user_anny_id(user_id: int):
    """
    Retrieve user anonymous id from database
    :param user_id:
    :return:
    """
    return users_collection.find_one({"user_id": user_id}).get('id', None)


def get_user_data_by_query(query: dict) -> dict | None:
    """Retrieve a user by query."""
    return users_collection.find_one(query)


def is_user_blocked(sender_id: str, recipient_id: int) -> bool:
    """
    Check if a user is blocked.
    :param sender_id: Anonymous ID of sender.
    :param recipient_id: User ID of recipient.
    :return: True if either user has blocked the other, False otherwise.
    """
    sender_data = get_user_data_by_query({"id": sender_id})
    recipient_data = get_user_data_by_query({"user_id": recipient_id})

    if not sender_data or not recipient_data:
        return False  # If data is missing, assume not blocked

    sender_blocklist = sender_data.get('blocklist', [])
    recipient_blocklist = recipient_data.get('blocklist', [])

    return sender_data['id'] in recipient_blocklist or recipient_data['id'] in sender_blocklist


def update_user_field(user_id: int, field: str, value: any) -> bool:
    """
    Update a specific user field with a new value.
    :param user_id: User ID.
    :param field: Field to update.
    :param value: New value for the field.
    :return: True if updated successfully, False otherwise.
    """
    try:
        result = users_collection.update_one({"user_id": user_id}, {"$set": {field: value}})
        return result.modified_count > 0
    except Exception as e:
        print(f"Failed to update user field: {e}")
        return False


def update_user_fields(user_id: int, fields: dict) -> bool:
    """
    Update multiple fields for a specific user.

    :param user_id: User ID.
    :param fields: A dictionary of fields to update.
    :return: True if updated successfully, False otherwise.
    """
    try:
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": fields}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Failed to update user fields: {e}")
        return False


def close_chats(user_id: int, reset_replying: bool = False) -> None:
    """
    Close all open chats for a user and optionally reset the replying state.
    :param user_id: User ID.
    :param reset_replying: Whether to reset replying state.
    """
    update_fields = {"chats.$[].open": False}
    if reset_replying:
        update_fields.update({"replying": False, "reply_target_message_id": "", "reply_target_user_id": ""})

    users_collection.update_one({"user_id": user_id}, {"$set": update_fields})


def add_seen_message(user_id, message_id: int):
    """
    Adds a message ID to the seen_messages array for a specific user.
    :param user_id: The ID of the user
    :param message_id: The ID of the message to mark as seen
    """
    users_collection.update_one(
        {
            "user_id": user_id
        },
        {
            "$addToSet": {
                "seen_messages": int(message_id)
            }
        }
    )


def get_seen_status(user_id, message_id: int):
    """
    Retrieve the seen status for the message from the user's document
    :param user_id: User ID of requester
    :param message_id: Message ID to check the seen status
    :return: Boolean indicating whether the message has been seen
    """
    # Query the database to get the 'seen_messages' for the user
    user_data = users_collection.find_one(
        {"user_id": user_id}
    )

    # Check if the 'seen_messages' array contains the given message_id
    if user_data:
        return int(message_id) in user_data.get('seen_messages', [])

    # If no data is found, assume the message has not been seen
    return False


def get_marked_status(text: str):
    if '#️⃣ #marked' in text:
        return True
    return False


def is_bot_status_off(user_id: str | int):
    if users_collection.find_one({"user_id": user_id}).get('is_bot_off', False):
        return True
    return False


def generate_anny_link(user_anny_id: str) -> str:
    """
    Generate a link to the bot for the user.
    :param user_anny_id: Anonymous ID of the user.
    :return: Bot link as a string.
    """
    bot_username = quote(config('BOT_USERNAME', cast=str))
    return f"https://t.me/{bot_username}?start={quote(user_anny_id)}"
