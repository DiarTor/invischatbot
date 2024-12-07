from decouple import config
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.database import users_collection


class UserAdministration:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.admin = config("ADMIN", cast=int)
    async def get_user_info(self, msg: Message):
        if not msg.from_user.id == self.admin:
            return
        parts = msg.text.split()
        if not len(parts) == 2:
            print("error")
        user_anny_id = parts[1]
        user_info = users_collection.find_one({"id": user_anny_id})
        if not user_info:
            print("user not found")
        await self.bot.send_message(msg.chat.id, user_info)