import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from decouple import config

logger = logging.getLogger(__name__)


class AsyncMongoConnection:
    def __init__(self):
        self._uri = config("MONGO_URI", cast=str)
        self._db_name = config("DATABASE_NAME", cast=str)
        self._user_collection = config("USERS_COLLECTION", cast=str)
        self._bot_collection = config("BOT_COLLECTION", cast=str)
        self._client: AsyncIOMotorClient = None
        self._db = None

    async def connect(self):
        try:
            self._client = AsyncIOMotorClient(
                self._uri,
                serverSelectionTimeoutMS=3000,
                socketTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=20,
                minPoolSize=5,
                retryWrites=True,
                w="majority",
            )
            await self._client.admin.command("ping")
            self._db = self._client[self._db_name]
            logger.info("✅ MongoDB connected successfully.")
        except Exception as e:
            logger.critical("❌ MongoDB connection failed: %s", e)
            raise

    @property
    def db(self):
        if not self._db:
            raise RuntimeError("MongoDB not connected. Call `await mongo.connect()` first.")
        return self._db

    @property
    def users_collection(self) -> AsyncIOMotorCollection:
        return self.db[self._user_collection]

    @property
    def bot_collection(self) -> AsyncIOMotorCollection:
        return self.db[self._bot_collection]


# Create a global instance to be initialized externally
mongo = AsyncMongoConnection()


async def init_bot_config(bot: AsyncIOMotorCollection):
    """
    Ensures default bot config and ban list documents exist.
    """
    default_documents = [
        {"_id": "bot_config", "admin": [], "total_messages": 0},
        {"_id": "ban_list", "banned_users": []},
        {"_id": "reactions", "reactions": []},
    ]

    for doc in default_documents:
        existing = await bot.find_one({"_id": doc["_id"]})
        if not existing:
            await bot.insert_one(doc)
            logger.info("✅ Inserted default config for: %s", doc["_id"])
        else:
            logger.info("ℹ️ Config for %s already exists.", doc["_id"])
