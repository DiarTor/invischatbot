import asyncio
import logging
from datetime import datetime, timedelta, timezone

from bot.database.database import mongo
from telebot.async_telebot import AsyncTeleBot


# Define your delete_message function properly
async def delete_message(bot: AsyncTeleBot, chat_id: int, message_id: int, second: int | float = 5):
    # Convert minutes to seconds and wait asynchronously
    await asyncio.sleep(second)  # Non-blocking wait
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.warning(f"❌ Error deleting message {message_id} in chat {chat_id}: {e}")
async def check_and_update_user(bot: AsyncTeleBot, user):
    try:
        profile = user.get("profile", {})
        updated_at = profile.get("updated_at", 0)
        last_update = datetime.fromtimestamp(updated_at)
        now = datetime.fromtimestamp(datetime.now().timestamp())

        if (now - last_update) >= timedelta(days=3):
            user_id = user.get("user_id")
            if not user_id:
                return

            chat = await bot.get_chat(user_id)
            changed = False

            for field in ["first_name", "last_name", "username"]:
                db_val = profile.get(field, "")
                tg_val = getattr(chat, field, "") or ""
                if db_val != tg_val:
                    profile[field] = tg_val
                    changed = True

            if changed:
                profile["updated_at"] = datetime.now().timestamp()
                await mongo.users_collection.update_one({"_id": user["_id"]}, {"$set": {"profile": profile}})
                logging.info(f"✅ Updated profile for user_id={user_id}")
            else:
                logging.info(f"ℹ️ No changes for user_id={user_id}")
    except Exception as e:
        logging.warning(f"❌ Error updating user_id={user.get('user_id')}: {e}")

async def profile_sync_loop(bot: AsyncTeleBot):
    while True:
        now = datetime.now()

        # Wait until next midnight
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (next_midnight - now).total_seconds()
        logging.info(f"⏳ Waiting {int(wait_seconds)}s until midnight to start sync...")
        await asyncio.sleep(wait_seconds)

        logging.info("🌙 Starting nightly profile sync...")
        users = await mongo.users_collection.find({}).to_list()
        for user in users:
            await check_and_update_user(bot, user)

        logging.info("✅ Sync finished. Sleeping for 3 days...")
        await asyncio.sleep(3 * 24 * 60 * 60)  # 3 days