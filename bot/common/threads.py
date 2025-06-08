import asyncio

from telebot.async_telebot import AsyncTeleBot


# Define your delete_message function properly
async def delete_message(bot: AsyncTeleBot, chat_id: int, message_id: int, second: int | float = 5):
    # Convert minutes to seconds and wait asynchronously
    await asyncio.sleep(second)  # Non-blocking wait
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Failed to delete message {message_id}: {e}")
