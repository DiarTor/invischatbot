from datetime import datetime

from decouple import config

from bot.common.utils import create_unique_id
from bot.database.database import users_collection, bot_collection


def user_exists(user_id: int) -> bool:
    """
    Check if the user exists in the database.
    :param user_id: User ID to check.
    :return: True if user exists, False otherwise.
    """
    return bool(users_collection.find_one({'user_id': user_id}))


def save_user_data(user_id: int, nickname: str = None, username=None, first_name=None, last_name=None) -> None:
    """
    Store user data in the database.
    :param first_name:
    :param last_name:
    :param username:
    :param user_id: User ID.
    :param nickname: Nickname of the user.
    """
    try:
        user_data = {
            "id": create_unique_id(),
            "user_id": user_id,
            "nickname": nickname,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "awaiting_nickname": False,
            "joined_at": datetime.timestamp(datetime.now()),
            "chats": [],
            "blocklist": [],
            "is_bot_off": False,
            "version": config('VERSION', cast=float),
            "first_time": True,
            "referred": False,
            "referred_by": '',
            "referrals": [],
        }
        users_collection.insert_one(user_data)
    except Exception as e:
        print(f"Failed to store user data: {e}")


def fetch_user_data_by_id(user_id: int) -> dict | None:
    """
    Retrieve user data from the database.
    :param user_id: User ID.
    :return: User data dictionary or None if not found.
    """
    return users_collection.find_one({"user_id": user_id}) or None


def get_user_id(user_anon_id: str):
    """
    Retrieve user id from database
    :param user_anon_id: the user anonymous id
    :return: the user id
    """
    return users_collection.find_one({"id": user_anon_id}).get('user_id', None)


def get_user_anon_id(user_id: int):
    """
    Retrieve user anonymous id from database
    :param user_id:
    :return:
    """
    return users_collection.find_one({"user_id": user_id}).get('id', None)


def fetch_user_data_by_query(query: dict) -> dict | None:
    """Retrieve a user by query."""
    return users_collection.find_one(query)


def update_user_fields(user_id: int, fields: dict | str, value: any = None, push: bool = False) -> bool:
    """
    Update user fields, either one field or multiple fields.

    :param user_id: User ID.
    :param fields: A single field (str) o update, or a dictionary of fields to update.
    :param value: New value for the field (only needed if updating a single field).
    :param push: If True, append the value to a list instead of replacing it (only for single field updates).
    :return: True if updated successfully, False otherwise.
    """
    try:
        if isinstance(fields, dict):
            # Update multiple fields
            update_operation = {"$set": fields}
        else:
            # Update a single field
            update_operation = {"$push": {fields: value}} if push else {"$set": {fields: value}}

        result = users_collection.update_one({"user_id": user_id}, update_operation, upsert=True)
        return result.modified_count > 0
    except Exception as e:
        print(f"Failed to update user fields: {e}")
        return False


def is_admin(user_id: int) -> bool:
    if bot_collection.find_one({"admin": user_id}) is None:
        return False
    return True


def get_admins() -> list:
    return bot_collection.find_one({"_id": "bot_config"}).get('admin', 0)


async def update_total_messages(count: int):
    bot_collection.update_one({"_id": "bot_config"}, {
        "$inc": {"total_messages": count}}, upsert=True)
