from telebot.types import CallbackQuery

from bot.admin.bot_administration import BotAdministration


class AdminCallbackHandler:
    def __init__(self, bot):
        self.bot = bot

    async def handle_callback(self, callback: CallbackQuery):
        callback_data = callback.data.split('-')[1:]
        if 'chat_stats' in callback_data:
            await BotAdministration(self.bot).get_bot_stats(callback.message)