from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.managers.start import StartBot
from bot.utils.language import get_response


class SupportManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def support(self, msg: Message):
        await StartBot(self.bot).start(msg, 'support')

    async def guide(self, msg: Message):
        await self.bot.send_message(msg.chat.id, get_response('support.guide'), parse_mode='Markdown')