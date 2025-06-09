"""
This module provides utility functions for interacting with the database.

It includes functions for managing user data, bot configuration, reactions, 
ban lists, and other database-related operations. These functions are designed 
to work asynchronously with MongoDB.

Key Features:
- User management: Fetch, update, and manage user data.
- Reaction handling: Store and retrieve emoji reactions for messages.
- Bot configuration: Update and retrieve bot-related settings.
- Ban management: Add or remove users from the ban list.
"""
from datetime import datetime
from typing import Any

from decouple import config
import pymongo.errors

from bot.common.utils import create_unique_id
from bot.database.database import mongo  # Your async mongo instance


async def user_exists(user_id: int) -> bool:
    """
    Check if the user exists in the database.
    """
    user = await mongo.users_collection.find_one({'user_id': user_id})
    return user is not None


async def save_user_data(user_id: int, nickname: str = None,
                         username=None, first_name=None, last_name=None) -> None:
    """
    Store user data in the database asynchronously using a structured schema.
    """
    try:
        now_ts = datetime.timestamp(datetime.now())
        user_data = {
            "anon_id": create_unique_id(),
            "user_id": user_id,
            "profile": {
                "nickname": nickname or "",
                "username": username or "",
                "first_name": first_name or "",
                "last_name": last_name or "",
            },
            "flags": {
                "awaiting_nickname": False,
                "send_without_link": False,
                "is_bot_off": False,
                "first_time": True,
            },
            "ban_info": {
                "is_banned": False,
                "banned_by": None,
                "banned_at": None,
            },
            "metadata": {
                "joined_at": now_ts,
                "last_interaction_time": now_ts,
                "version": float(config('VERSION', default=1.0)),

            },
            "referral_info": {
                "referred": False,
                "referred_by": '',
                "referrals": [],
            },
            "lists": {
                "chats": [],
                "blocklist": [],
            }
        }

        await mongo.users_collection.insert_one(user_data)

    except pymongo.errors.PyMongoError as e:
        print(f"Failed to store user data: {e}")



# -----------------------
# 🛠 Utility Functions
# -----------------------

async def _find_one(collection, query: dict) -> dict | None:
    """Generic async wrapper to find one document."""
    return await collection.find_one(query)

async def _update_one(collection, query: dict, update: dict) -> bool:
    """Generic async wrapper to update one document."""
    try:
        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count > 0
    except pymongo.errors.PyMongoError as e:
        print(f"Update error: {e}")
        return False

# -----------------------
# 👤 User Functions
# -----------------------

async def fetch_user_data_by_user_id(user_id: int) -> dict | None:
    """Retrieve a user's data by their user ID."""
    return await _find_one(mongo.users_collection, {"user_id": user_id})

async def fetch_user_data_by_query(query: dict) -> dict | None:
    """Retrieve a user's data using a custom query."""
    return await _find_one(mongo.users_collection, query)

async def get_user_field(search_field: str, search_value: Any, return_field: str) -> Any:
    """Generic function to retrieve a user field by searching another field."""
    user = await _find_one(mongo.users_collection, {search_field: search_value})
    return user.get(return_field) if user else None

async def get_user_id(user_anon_id: str) -> Any:
    """Retrieve user ID from anonymous ID."""
    return await get_user_field("id", user_anon_id, "user_id")

async def get_user_anon_id(user_id: int) -> Any:
    """Retrieve anonymous ID from user ID."""
    return await get_user_field("user_id", user_id, "id")

async def get_user_anon_id_by_username(username: str) -> str | None:
    """Retrieve anonymous ID of a user by their username."""
    user = await _find_one(mongo.users_collection, {"username": username})
    return user['id'] if user else None

async def update_user_fields(user_id: int, fields: dict | str, value: Any = None,
                            push: bool = False) -> bool:
    """Update user fields. Supports single key or full dict. Use `push=True` to append to arrays."""
    query = {"user_id": user_id}
    if isinstance(fields, dict):
        update = {"$set": fields}
    else:
        update = {"$push" if push else "$set": {fields: value}}
    return await _update_one(mongo.users_collection, query, update)

async def update_last_interaction_time(user_id: int):
    """Update user's last interaction timestamp."""
    timestamp = datetime.timestamp(datetime.now())
    await update_user_fields(user_id, "last_interaction_time", timestamp)

async def is_user_banned(user_id: int) -> bool:
    """Check if the user is banned."""
    user = await _find_one(mongo.users_collection, {"user_id": user_id})
    return bool(user and user.get("is_banned"))

async def close_metadata(user_id: int, field: str = None):
    """Clear metadata flags for the user. Can target a single field or all."""
    if field:
        await update_user_fields(user_id, field, False)
    else:
        await update_user_fields(user_id, {
            "awaiting_nickname": False,
            "send_without_link": False
        })

# -----------------------
# 🤖 Bot Configuration
# -----------------------

async def update_bot_fields(fields: dict | str, value: Any = None) -> bool:
    """Update bot configuration fields."""
    query = {"_id": "bot_config"}
    if isinstance(fields, dict):
        update = {"$set": fields}
    else:
        update = {"$set": {fields: value}}
    return await _update_one(mongo.bot_collection, query, update)

async def update_total_messages(count: int):
    """Increment the total message count in bot config."""
    await mongo.bot_collection.update_one(
        {"_id": "bot_config"},
        {"$inc": {"total_messages": count}},
        upsert=True
    )

async def get_admins() -> list:
    """Retrieve the list of admin user IDs from config."""
    bot_config = await _find_one(mongo.bot_collection, {"_id": "bot_config"})
    return bot_config.get("admin", []) if config else []

async def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    return user_id in await get_admins()

async def get_support_group() -> str | None:
    """Get the support channel ID from config."""
    bot_config = await _find_one(mongo.bot_collection, {"_id": "bot_config"})
    return bot_config.get("support_channel") if config else None

# -----------------------
# ⛔ Ban Management
# -----------------------

async def update_ban_list(user_id: int, action: str) -> bool:
    """Ban or unban a user."""
    try:
        if action == 'ban':
            await mongo.bot_collection.update_one(
                {"_id": "ban_list"}, {"$addToSet": {"banned_users": user_id}}, upsert=True)
        elif action == 'unban':
            await mongo.bot_collection.update_one(
                {"_id": "ban_list"}, {"$pull": {"banned_users": user_id}}, upsert=True)
        return True
    except pymongo.errors.PyMongoError as e:
        print(f"Failed to update ban list: {e}")
        return False

# -----------------------
# 💬 Reactions
# -----------------------

async def add_reaction(user_id: int, message_id: int, emoji: str):
    """Store a user's emoji reaction to a message."""
    await mongo.bot_collection.update_one(
        {"_id": "reactions"},
        {"$set": {f"reactions.{user_id}.{message_id}": emoji}},
        upsert=True
    )

async def get_reactions(user_id: int, message_id: int) -> str:
    """Get a user's emoji reaction for a message."""
    reactions = await _find_one(mongo.bot_collection, {"_id": "reactions"})
    return reactions.get("reactions", {}).get(str(user_id),
                        {}).get(str(message_id),
                        'هیچ ریاکشنی ندادی') if reactions else 'هیچ ریاکشنی ندادی'
