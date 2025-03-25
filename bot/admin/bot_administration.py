from datetime import datetime, timedelta

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.database.database import users_collection
from bot.languages.response import get_response


class BotAdministration:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def get_chats_stats(self, msg: Message):
        chat_counts = self.get_chat_counts()

        # Prepare formatted response data
        stats_data = {
            "chat_today": chat_counts["today"],
            "chat_week": chat_counts["this_week"],
            "chat_month": chat_counts["this_month"],
            "chat_year": chat_counts["this_year"],
            "chat_all_time": chat_counts["all_time"],
        }

        # Send the status message
        await self.bot.send_message(
            msg.chat.id,
            get_response("admin.stats.chats", **stats_data),
            parse_mode="Markdown"
        )

    async def get_users_stats(self, msg: Message):
        user_counts = self.get_users_count()
        stats_data = {
            "today": user_counts["today"],
            "week": user_counts["this_week"],
            "month": user_counts["this_month"],
            "year": user_counts["this_year"],
            "all_time": user_counts["all_time"],

        }
        # Send the status message
        await self.bot.send_message(
            msg.chat.id,
            get_response("admin.stats.users", **stats_data),
            parse_mode="Markdown")

    @staticmethod
    def get_users_count():
        # Get the current datetime and convert to UNIX timestamp
        now = datetime.now()

        # Calculate the start times as UNIX timestamps
        start_today = datetime(now.year, now.month, now.day).timestamp()
        start_week = (datetime(now.year, now.month, now.day) - timedelta(
            days=now.weekday())).timestamp()  # Start of the current week (Monday)
        start_month = datetime(now.year, now.month, 1).timestamp()  # First day of the current month
        start_year = datetime(now.year, 1, 1).timestamp()  # First day of the current year

        # Query the MongoDB collection to count users in each timeframe
        all_time = users_collection.count_documents({})
        today_count = users_collection.count_documents({"joined_at": {"$gte": start_today}})
        week_count = users_collection.count_documents({"joined_at": {"$gte": start_week}})
        month_count = users_collection.count_documents({"joined_at": {"$gte": start_month}})
        year_count = users_collection.count_documents({"joined_at": {"$gte": start_year}})

        return {
            'all_time': all_time,
            'today': today_count,
            'this_week': week_count,
            'this_month': month_count,
            'this_year': year_count
        }

    @staticmethod
    def get_chat_counts():
        # Current datetime
        now = datetime.now()

        # Define the start times for each period
        start_of_today = datetime(now.year, now.month, now.day)
        start_of_week = start_of_today - timedelta(days=start_of_today.weekday())
        start_of_month = datetime(now.year, now.month, 1)
        start_of_year = datetime(now.year, 1, 1)

        # Convert the start times to timestamps
        timestamp_today = start_of_today.timestamp()
        timestamp_week = start_of_week.timestamp()
        timestamp_month = start_of_month.timestamp()
        timestamp_year = start_of_year.timestamp()

        # Initialize counters
        counts = {
            'today': 0,
            'this_week': 0,
            'this_month': 0,
            'this_year': 0,
            'all_time': 0
        }

        # Retrieve all user documents
        user_documents = users_collection.find()

        # Loop through each user document and count chats based on 'chat_created_at' timestamp
        for user_doc in user_documents:
            for chat in user_doc.get("chats", []):
                chat_created_at = chat.get("chat_created_at")
                if chat_created_at is not None:
                    # Increment counts based on time periods
                    counts['all_time'] += 1
                    if chat_created_at >= timestamp_year:
                        counts['this_year'] += 1
                    if chat_created_at >= timestamp_month:
                        counts['this_month'] += 1
                    if chat_created_at >= timestamp_week:
                        counts['this_week'] += 1
                    if chat_created_at >= timestamp_today:
                        counts['today'] += 1

        return counts
