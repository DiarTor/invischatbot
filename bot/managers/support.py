from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from bot.languages.response import get_response
from bot.common.database_utils import get_support_group

class SupportManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.suppurt_group = get_support_group()

    async def support(self, msg: Message):
        "Handle the support command to start a support session."
        #TODO: Implement support session logic


    async def guide(self, msg: Message):
        await self.bot.send_message(msg.chat.id, get_response('support.guide'), parse_mode='Markdown')
