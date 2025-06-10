import logging
import uuid
from urllib.parse import quote

import colorlog
from bot.database.database import mongo
from decouple import config


async def create_unique_id() -> str:
    """Generate a unique 10-character ID."""
    while True:
        anon_id = f"{str(uuid.uuid4())[:5]}{str(uuid.uuid4().int)[-5:]}"
        if anon_id not in await mongo.users_collection.distinct("anon_id"):
            return anon_id


def generate_anon_link(anon_id: str) -> str:
    """
    Generate a link to the bot for the user.
    :param anon_id: Anonymous ID of the user.
    :return: Bot link as a string.
    """
    bot_username = quote(config('BOT_USERNAME', cast=str))
    return f"https://t.me/{bot_username}?start={quote(anon_id)}"

def setup_logger():
    """Sets up the logger with color support."""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))
    local_logger = colorlog.getLogger()
    local_logger.addHandler(handler)
    local_logger.setLevel(logging.INFO)  # Set to DEBUG for detailed logs
    return local_logger

logger = setup_logger()
