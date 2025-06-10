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
from typing import Any, Dict, Optional

from decouple import config
import pymongo.errors
from motor.motor_asyncio import AsyncIOMotorCollection
from bot.common.utils import create_unique_id
from bot.common.utils import logger
from bot.database.database import mongo
from telebot.async_telebot import AsyncTeleBot

class UserDataManager:
    """Manages the user data"""
    def __init__(self, user_id: int, collection: AsyncIOMotorCollection):
        self.user_id = user_id
        self.now = datetime.now().timestamp()
        self.collection = collection
        self.version = config('VERSION', default=1.0, cast=float)

    async def save_user(self, **profile_data):
        """Stores the user data on join"""
        update_data = {
                "$setOnInsert": {
                    "anon_id": await create_unique_id(),
                    "user_id": self.user_id,
                    "flags": {
                        "awaiting_nickname": False,
                        "send_without_link": False,
                        "is_bot_off": False,
                        "first_time": True,
                        "replying": False,
                    },
                    "ban_info": {
                        "is_banned": False,
                        "banned_by": None,
                        "banned_at": None,
                        },
                    "metadata": {
                        "joined_at": self.now,
                        "last_intraction": self.now,
                        "version": float(config('VERSION', default=1.0)),
                    },
                    "referral_info": {
                        "referred": False,
                        "referred_by": '',
                        "referrals": [],
                    },
                    "chatting": {
                        "chats": [],
                        "replying": {
                            "reply_target_message_id": '',
                            "reply_target_user_id": 0,
                        },
                        "blocklist": [],
                    },
                    "profile": self.normalize_profile(profile_data)
                },
            }
        try:
            result = await self.collection.update_one(
                {'user_id': self.user_id},
                update_data,
                upsert=True
            )
            return result.modified_count > 0
        except pymongo.errors.DuplicateKeyError:
            # handle race condition
            return await self.fetch_user()

    async def update_profile(self, **changes) -> bool:
        """
        Updates only profile fields.
        Returns True if modifications were made.
        """
        valid_fields = {
            "username", 
            "first_name", "last_name"
        }

        updates = {
            f"profile.{k}": v
            for k, v in changes.items()
            if k in valid_fields and v is not None
        }

        if not updates:
            return False

        updates["profile.updated_at"] = self.now

        result = await self.collection.update_one(
            {"user_id": self.user_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def toggle_flag(self, flag_name: str, value: Optional[bool] = None) -> bool:
        """
        Sets or toggles boolean flags.
        Returns True if changes were made.
        """
        valid_flags = {
            "awaiting_nickname", 
            "send_without_link",
            "is_bot_off",
            "first_time"
        }

        if flag_name not in valid_flags:
            return False

        update = {"$set" if value is not None else "$bit": {
            f"flags.{flag_name}": value if value is not None else {"xor": 1}
        }}

        result = await self.collection.update_one(
            {"user_id": self.user_id},
            update
        )
        return result.modified_count > 0

    async def update_metadata(self, **updates) -> bool:
        """
        Updates metadata fields for the user.
        Only allows updates to specific metadata fields with proper validation.
        """
        allowed_fields = {
            "last_interaction": datetime,
            "version": (float, int),
        }

        valid_updates = {}
        for field, value in updates.items():
            if field in allowed_fields:
                expected_type = allowed_fields[field]

                if expected_type is datetime and not isinstance(value, datetime):
                    if isinstance(value, (int, float)):
                        value = datetime.fromtimestamp(value)
                    else:
                        continue

                elif not isinstance(value, expected_type):
                    if not (isinstance(expected_type, tuple) and isinstance(value, expected_type)):
                        continue

                valid_updates[f"metadata.{field}"] = value

        if not valid_updates:
            return False

        try:
            result = await self.collection.update_one(
                {"user_id": self.user_id},
                {"$set": valid_updates}
            )
            return result.modified_count > 0
        except pymongo.errors.PyMongoError as e:
            logger.error("Failed to update metadata for user %s: %s", self.user_id, e)
            return False

    async def fetch_user(self) -> Optional[Dict[str, Any]]:
        """Retrieves full user document"""
        return await self.collection.find_one({"user_id": self.user_id})

    async def exists(self) -> bool:
        """Check if the user exists in the database"""
        return await self.fetch_user() is not None

    async def is_banned(self) -> bool:
        """Check if the user is banned."""
        user = await self.fetch_user()
        return bool(user and user.get("ban_info", {}).get("is_banned", False))

    async def update_last_interaction(self) -> bool:
        """Update user's last interaction timestamp."""
        return await self.update_metadata(last_interaction=self.now)

    async def update_fields(self, fields: dict | str, value: Any = None,
                            push: bool = False) -> bool:
        """Update user fields. Supports single key & full dict. Use push=True to append to array."""
        if isinstance(fields, dict):
            update = {"$set": fields}
        else:
            update = {"$push" if push else "$set": {fields: value}}

        result = await self.collection.update_one(
            {"user_id": self.user_id},
            update
        )
        return result.modified_count > 0

    async def close_metadata(self, field: str = None):
        """Clear metadata flags for the user. Can target a single field or all."""
        if field:
            await self.update_fields(f"flags.{field}", False)
        else:
            await self.update_fields({
                "flags.awaiting_nickname": False,
                "flags.send_without_link": False,
                "flags.replying": False,
            })

    async def is_bot_disabled(self) -> bool:
        """
        Check if the user has disabled the bot.
        Returns True if the bot is turned off for this user.
        """
        user = await self.fetch_user()
        return user.get('flags', {}).get('is_bot_off', False) if user else False

    async def get_anon_id(self) -> str:
        """Get user anon_id with their user_id"""
        return await self.fetch_user().get('anon_id', '')

    def normalize_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures consistent profile structure"""
        return {
            "nickname": data.get("nickname", ""),
            "username": data.get("username", ""),
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "updated_at": data.get("updated_at", self.now)
        }

    @classmethod
    async def get_anon_id_by_username(
        cls,
        collection: AsyncIOMotorCollection,
        username: str
    ) -> Optional[str]:
        """Retrieve anonymous ID of a user by their username."""
        user = await collection.find_one({"profile.username": username})
        return user.get("anon_id") if user else None


class BotDataManager:
    """Manages bot-wide operations and configurations"""
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def update_fields(self, fields: dict | str, value: Any = None) -> bool:
        """Update bot configuration fields."""
        query = {"_id": "bot_config"}
        if isinstance(fields, dict):
            update = {"$set": fields}
        else:
            update = {"$set": {fields: value}}
        result = await self.collection.update_one(query, update)
        return result.modified_count > 0

    async def update_total_messages(self, count: int):
        """Increment the total message count in bot config."""
        await self.collection.update_one(
            {"_id": "bot_config"},
            {"$inc": {"total_messages": count}},
            upsert=True
        )

    async def get_admins(self) -> list:
        """Retrieve the list of admin user IDs from config."""
        bot_config = await self.collection.find_one({"_id": "bot_config"})
        return bot_config.get("admin", []) if bot_config else []

    async def is_admin(self, user_id: int) -> bool:
        """Check if the user is an admin."""
        return user_id in await self.get_admins()

    async def get_support_group(self) -> str | None:
        """Get the support channel ID from config."""
        bot_config = await self.collection.find_one({"_id": "bot_config"})
        return bot_config.get("support_channel") if bot_config else None

    async def update_ban_list(self, user_id: int, action: str) -> bool:
        """Ban or unban a user."""
        try:
            if action == 'ban':
                await self.collection.update_one(
                    {"_id": "ban_list"}, {"$addToSet": {"banned_users": user_id}}, upsert=True)
            elif action == 'unban':
                await self.collection.update_one(
                    {"_id": "ban_list"}, {"$pull": {"banned_users": user_id}}, upsert=True)
            return True
        except pymongo.errors.PyMongoError as e:
            logger.error(f"Failed to update ban list: {e}")
            return False

class ChatDataManager:
    """Handles all chat-related data including reactions and chat states"""
    def __init__(self, user_collection: AsyncIOMotorCollection, bot_collection: AsyncIOMotorCollection):
        self.user_collection = user_collection
        self.bot_collection = bot_collection

    # ----- Chat State Management -----
    async def close_chats(self, user_id: int, reset_replying: bool = False) -> bool:
        """
        Close all open chats for a user and optionally reset the replying state.
        Returns True if modifications were made.
        """
        update_fields = {"chatting.chats.$[].open": False}
        if reset_replying:
            update_fields.update({
                "chatting.replying.reply_target_message_id": "",
                "chatting.replying.reply_target_user_id": 0
            })

        result = await self.user_collection.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )
        return result.modified_count > 0

    async def mark_message_seen(self, user_id: int, message_id: int) -> bool:
        """
        Record that a user has seen a specific message.
        Returns True if the message was newly added to seen messages.
        """
        result = await self.user_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"metadata.seen_messages": int(message_id)}}
        )
        return result.modified_count > 0

    async def has_seen_message(self, user_id: int, message_id: int) -> bool:
        """Check if a user has seen a specific message"""
        user_data = await self.user_collection.find_one(
            {"user_id": user_id},
            {"metadata.seen_messages": 1}
        )
        return int(message_id) in user_data.get("metadata", {}).get("seen_messages", []) if user_data else False

    # ----- Reaction Management -----
    async def add_reaction(
        self,
        user_id: int,
        message_id: int,
        emoji: str,
    ) -> None:
        """Store a user's reaction to a message"""
        await self.bot_collection.update_one(
            {"_id": "reactions"},
            {"$set": {f"reactions.{user_id}.{message_id}": emoji}},
            upsert=True
        )

    async def get_reaction(
        self,
        user_id: int,
        message_id: int,
        default_response: str = 'هیچ ریاکشنی ندادی'
    ) -> str:
        """Retrieve a user's reaction to a specific message"""
        reactions = await self.bot_collection.find_one({"_id": "reactions"})
        if not reactions:
            return default_response
            
        return reactions.get("reactions", {})\
                       .get(str(user_id), {})\
                       .get(str(message_id), default_response)

    # ----- Utility Methods -----
    @staticmethod
    def is_text_marked(text: str) -> bool:
        """Check if text contains marking indicator"""
        return '📍 #نشان' in text

    @staticmethod
    def extract_marked_content(text: str) -> str:
        """Extract content after marking indicator"""
        if '📍 #نشان' in text:
            return text.split('📍 #نشان', 1)[1].strip()
        return text

class AdManager:
    """Handles all advertising-related functionality including channel promotions and links"""
    def __init__(self, bot: AsyncTeleBot, channel_ids: list[int]):
        self.bot = bot
        self.channel_ids = channel_ids

    async def is_subscribed(self, user_id: int) -> bool:
        """
        Check if user is subscribed to all required channels.
        Returns True if subscribed to all channels.
        """
        for channel_id in self.channel_ids:
            try:
                chat_member = await self.bot.get_chat_member(
                    chat_id=channel_id,
                    user_id=user_id
                )
                if chat_member.status not in ["member", "administrator", "creator"]:
                    return False
            except Exception as e:
                logger.error("Failed to check subscription for %s: %s", user_id, e)
                return False
        return True


# -----------------------
# 🛠 Utility Functions
# -----------------------

async def find_one(collection, query: dict) -> dict | None:
    """Generic async wrapper to find one document."""
    return await collection.find_one(query)

async def update_one(collection, query: dict, update: dict) -> bool:
    """Generic async wrapper to update one document."""
    try:
        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count > 0
    except pymongo.errors.PyMongoError as e:
        logger.error("Update error: %s", e)
        return False

async def get_user_id(user_anon_id: str) -> Any:
    """Retrieve user ID from anonymous ID."""
    return await find_one(mongo.users_collection, {'anon_id': user_anon_id}).get('user_id', '')
