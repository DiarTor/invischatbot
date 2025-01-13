import asyncio

from telebot.async_telebot import AsyncTeleBot


async def delete_message(bot: AsyncTeleBot, chat_id: int, message_id: int, seconds: int = 300):
    await asyncio.sleep(seconds)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)
