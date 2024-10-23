from decouple import config
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(config('MONGO_URI', cast=str))
db = client.get_database(config('DATABASE_NAME', cast=str))
active_chats_collection = db.get_collection(config('ACTIVE_CHAT_COLLECTION', cast=str))
