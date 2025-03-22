from telebot.types import InlineKeyboardButton

from bot.common.keyboard import KeyboardMarkupGenerator


class Keyboard(KeyboardMarkupGenerator):

    def main_panel(self):
        buttons = [InlineKeyboardButton('💬 آمار چت ها', callback_data='admin-chat_stats')]

        return self._create_inline_keyboard(buttons)