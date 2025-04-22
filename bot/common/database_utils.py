from datetime import datetime

from decouple import config
import pymongo

from bot.common.utils import create_unique_id
from bot.database.database import users_collection, bot_collection


async def user_exists(user_id: int) -> bool:
    """
    Check if the user exists in the database.
    :param user_id: User ID to check.
    :return: True if user exists, False otherwise.
    """
    return bool(users_collection.find_one({'user_id': user_id}))


async def save_user_data(user_id: int, nickname: str = None, username=None, first_name=None, last_name=None) -> None:
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
            "is_banned": False,
            "banned_by": None,
            "banned_at": None,
        }
        users_collection.insert_one(user_data)
    except pymongo.errors.PyMongoError as e:
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


async def update_user_fields(user_id: int, fields: dict | str, value: any = None, push: bool = False) -> bool:
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
    except pymongo.errors.PyMongoError as e:
        print(f"Failed to update user fields: {e}")
        return False

def update_bot_fields(fields: dict | str, value: any = None) -> bool:
    """
    Update bot fields, either one field or multiple fields.

    :param fields: A single field (str) to update, or a dictionary of fields to update.
    :param value: New value for the field (only needed if updating a single field).
    :return: True if updated successfully, False otherwise.
    """
    try:
        if isinstance(fields, dict):
            # Update multiple fields
            update_operation = {"$set": fields}
        else:
            # Update a single field
            update_operation = {"$set": {fields: value}}

        result = bot_collection.update_one({"_id": "bot_config"}, update_operation, upsert=True)
        return result.modified_count > 0
    except pymongo.errors.PyMongoError as e:
        print(f"Failed to update bot fields: {e}")
        return False

async def update_ban_list(user_id: int, action: str) -> bool:
    """
    Update the ban list in the database.

    :param user_id: User ID to be banned or unbanned.
    :param action: Action to perform ('ban' or 'unban').
    :return: True if updated successfully, False otherwise.
    """
    try:
        if action == 'ban':
            bot_collection.update_one({"_id": "ban_list"}, {"$addToSet": {"banned_users": user_id}}, upsert=True)
        elif action == 'unban':
            bot_collection.update_one({"_id": "ban_list"}, {"$pull": {"banned_users": user_id}}, upsert=True)
        return True
    except pymongo.errors.PyMongoError as e:
        print(f"Failed to update ban list: {e}")
        return False
def is_user_banned(user_id: int) -> bool:
    """
    Check if a user is banned.
    :param user_id: User ID to check.
    :return: True if user is banned, False otherwise.
    """
    if users_collection.find_one({"user_id": user_id}).get('is_banned'):
        return True
    return False

def is_admin(user_id: int) -> bool:
    if bot_collection.find_one({"admin": user_id}) is None:
        return False
    return True


async def get_admins() -> list:
    return bot_collection.find_one({"_id": "bot_config"}).get('admin', 0)


async def update_total_messages(count: int):
    bot_collection.update_one({"_id": "bot_config"}, {
        "$inc": {"total_messages": count}}, upsert=True)
