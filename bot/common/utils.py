import uuid
from urllib.parse import quote
from bot.database.database import mongo
from decouple import config


async def create_unique_id() -> str:
    """Generate a unique 10-character ID."""
    while True:
        anon_id = f"{str(uuid.uuid4())[:5]}{str(uuid.uuid4().int)[-5:]}"
        if anon_id not in await mongo.users_collection.distinct("id"):
            return anon_id


def generate_anon_link(anon_id: str) -> str:
    """
    Generate a link to the bot for the user.
    :param anon_id: Anonymous ID of the user.
    :return: Bot link as a string.
    """
    bot_username = quote(config('BOT_USERNAME', cast=str))
    return f"https://t.me/{bot_username}?start={quote(anon_id)}"
