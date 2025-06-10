import logging
import asyncio
from typing import Optional, Tuple
from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
class AsyncMongoConnection:
    def __init__(self):
        self._uri = config("MONGO_URI", cast=str)
        self._db_name = config("DATABASE_NAME", cast=str)
        self._user_collection = config("USERS_COLLECTION", cast=str)
        self._bot_collection = config("BOT_COLLECTION", cast=str)
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._connect_lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._db is not None


    async def connect(self) -> Tuple[bool, Optional[Exception]]:
        """
        Safe connection method with locking
        Returns: (success, error)
        """
        async with self._connect_lock:
            if self.is_connected:
                return True, None

            try:
                self._client = AsyncIOMotorClient(
                    self._uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=30000,
                    maxPoolSize=50,
                    minPoolSize=10,
                    retryWrites=True,
                    retryReads=True,
                    w="majority",
                    appname="telebot_db",
                    heartbeatFrequencyMS=30000,
                )
                
                # Verify connection actually works
                await asyncio.wait_for(
                    self._client.admin.command('ping'),
                    timeout=3
                )
                
                self._db = self._client[self._db_name]
                logger.info("MongoDB connection established")
                return True, None
                
            except Exception as e:
                await self._cleanup()
                logger.critical("MongoDB connection failed: %s", str(e), exc_info=True)
                return False, e

    async def _cleanup(self):
        """Proper resource cleanup"""
        if self._client and not self._client.is_closed:
            self._client.close()
        self._client = None
        self._db = None

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Safe database accessor with connection check"""
        if not self.is_connected:
            raise RuntimeError("Database not connected. Call await connect() first.")
        return self._db

    @property
    def users_collection(self) -> AsyncIOMotorCollection:
        """Thread-safe collection accessor"""
        return self.db[self._user_collection]

    @property
    def bot_collection(self) -> AsyncIOMotorCollection:
        """Thread-safe collection accessor"""
        return self.db[self._bot_collection]

    async def __aenter__(self):
        """Support for async context manager"""
        success, error = await self.connect()
        if not success:
            raise error
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Automatic cleanup on context exit"""
        await self._cleanup()


# Global instance with lazy initialization
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
