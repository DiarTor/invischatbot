from telebot.types import CallbackQuery

from bot.admin.bot_administration import BotAdministration
from bot.admin.adminstration import Admin


class AdminCallbackHandler:
    """Handles admin-related callbacks for the bot."""
    def __init__(self, bot):
        self.bot = bot

    async def handle_callback(self, callback: CallbackQuery):
        """Handle admin-related callbacks."""
        callback_data = callback.data.split('-')[1:]
        if 'chats_stats' in callback_data:
            await BotAdministration(self.bot).get_chats_stats(callback.message)
        elif 'users_stats' in callback_data:
            await BotAdministration(self.bot).get_users_stats(callback.message)
        elif 'ban_list' in callback_data:
            await BotAdministration(self.bot).get_ban_list(callback.message)
        elif 'broadcast' in callback_data:
            await Admin(self.bot).activate_broadcast(callback.message)
        elif 'cancel' in callback_data:
            await Admin(self.bot).cancel_broadcast(callback.message)
