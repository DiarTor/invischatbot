import logging
import uuid
from urllib.parse import quote
import subprocess
import colorlog
from bot.database.database import mongo
from decouple import config
from datetime import datetime

import jdatetime


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

def convert_timestamp_to_date(timestamp, show="date", calendar_type="gregorian"):
    """
    Convert a timestamp to Jalali (Persian) or Gregorian date and time format.

    Parameters:
    - timestamp: The input timestamp (in seconds since epoch).
    - show: Determines the format of the output. Options are:
        - "date": Show only the date (e.g., 1403/01/01 or 2024/01/01)
        - "time": Show only the time (e.g., 14:30:00)
        - "datetime": Show both date and time (e.g., 1403/01/01 14:30:00 or 2024/01/01 14:30:00)
    - calendar_type: The calendar format to use. Options are:
        - "jalali": Use the Jalali (Persian) calendar
        - "gregorian": Use the Gregorian calendar

    Returns:
    - A formatted string according to the selected `show` and `calendar_type` options.
    """
    # Convert the timestamp to the appropriate datetime object
    if calendar_type == "jalali":
        date_time = jdatetime.datetime.fromtimestamp(timestamp)
    elif calendar_type == "gregorian":
        date_time = datetime.fromtimestamp(timestamp)
    else:
        raise ValueError("Invalid `calendar_type`. Choose from 'jalali' or 'gregorian'.")

    # Format according to the `show` parameter
    if show == "date":
        return date_time.strftime("%Y/%m/%d")
    elif show == "time":
        return date_time.strftime("%H:%M:%S")
    elif show == "datetime":
        return date_time.strftime("%Y/%m/%d %H:%M:%S")
    else:
        raise ValueError("Invalid `show` option. Choose from 'date', 'time', or 'datetime'.")
    

def get_last_commit():
    try:
        result = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=format:%h'],
            stderr=subprocess.STDOUT
        )
        return result.decode('utf-8')
    except Exception:
        return "Commit info not available (Git not installed on server)."


def get_latest_tag():
    try:
        result = subprocess.check_output(
            ['git', 'describe', '--tags', '--abbrev=0'],
            stderr=subprocess.STDOUT
        )
        return result.decode('utf-8').strip()
    except Exception:
        return "No tags found."