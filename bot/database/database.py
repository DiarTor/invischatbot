import logging
from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

logger = logging.getLogger(__name__)
class AsyncMongoConnection:
    def __init__(self):
        self._uri = config("MONGO_URI", cast=str)
        self._db_name = config("DATABASE_NAME", cast=str)
        self._user_collection = config("USERS_COLLECTION", cast=str)
        self._bot_collection = config("BOT_COLLECTION", cast=str)

        # Initialize client and db immediately
        self._client = AsyncIOMotorClient(self._uri)
        self._db = self._client[self._db_name]

    @property
    def users_collection(self) -> AsyncIOMotorCollection:
        """Get the users collection"""
        return self._db[self._user_collection]

    @property
    def bot_collection(self) -> AsyncIOMotorCollection:
        """Get the bot collection"""
        return self._db[self._bot_collection]

    async def close(self):
        """Close the connection when done"""
        if self._client:
            self._client.close()


# Global instance with lazy initialization
mongo = AsyncMongoConnection()


async def init_bot_config(bot: AsyncIOMotorCollection):
    """
    Ensures default bot config and ban list documents exist.
    """
    default_documents = [
    {
        "_id": "bot_config",
        "admin_user_ids": [],
        "statistics": {
            "total_messages": 0
        }
    },
    {
        "_id": "bot_bans",
        "banned_user_ids": []
    },
    ]

    for doc in default_documents:
        existing = await bot.find_one({"_id": doc["_id"]})
        if not existing:
            await bot.insert_one(doc)
            logger.info("✅ Inserted default config for: %s", doc["_id"])
        else:
            logger.info("ℹ️ Config for %s already exists.", doc["_id"])
