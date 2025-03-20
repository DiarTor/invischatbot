import uuid
from urllib.parse import quote

from decouple import config


def create_unique_id() -> str:
    """Generate a unique 10-character ID."""
    return f"{str(uuid.uuid4())[:5]}{str(uuid.uuid4().int)[-5:]}"


def generate_anon_link(anon_id: str) -> str:
    """
    Generate a link to the bot for the user.
    :param anon_id: Anonymous ID of the user.
    :return: Bot link as a string.
    """
    bot_username = quote(config('BOT_USERNAME', cast=str))
    return f"https://t.me/{bot_username}?start={quote(anon_id)}"
