import asyncio
from telebot.async_telebot import AsyncTeleBot

# Define your delete_message function properly
async def delete_message(bot: AsyncTeleBot, chat_id: int, message_id: int, minutes: int = 5):
    # Convert minutes to seconds and wait asynchronously
    await asyncio.sleep(minutes * 60)  # Non-blocking wait
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Message {message_id} deleted successfully.")
    except Exception as e:
        print(f"Failed to delete message {message_id}: {e}")