from decouple import config
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

# Connect to MongoDB
client = MongoClient(config('MONGO_URI', cast=str))
db = client.get_database(config('DATABASE_NAME', cast=str))
users_collection = db.get_collection(config('USERS_COLLECTION', cast=str))
bot_collection = db.get_collection(config('BOT_COLLECTION', cast=str))

def init_bot_config():
    default_bot_config = {
        "_id": "bot_config",
        "admin": [],
        "total_messages": 0
    }

    default_ban_list = {
        "_id": "ban_list",
        "banned_users": []
    }

    # Check and insert if not exists
    for doc in [default_bot_config, default_ban_list]:
        if bot_collection.find_one({"_id": doc["_id"]}) is None:
            bot_collection.insert_one(doc)
            logger.info("Inserted default config for: %s", doc["_id"])
        else:
            logger.info("Config for %s already exists.", doc["_id"])
