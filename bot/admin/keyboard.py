from telebot.types import InlineKeyboardButton

from bot.common.keyboard import KeyboardMarkupGenerator


class Keyboard(KeyboardMarkupGenerator):

    def main_panel(self):
        buttons = [
            [
                InlineKeyboardButton('💬 آمار چت ها', callback_data='admin-chats_stats'),
                InlineKeyboardButton('👥 آمار کاربران', callback_data='admin-users_stats')
            ],
            [
                InlineKeyboardButton('❌ بن لیست', callback_data='admin-ban_list'),
            ],
            [
                InlineKeyboardButton('🔊 پیام همگانی', callback_data='admin-broadcast'),
            ]
        ]

        return self._create_list_inline_keyboard(buttons)

    def broadcast_buttons(self):
        buttons = [
            [
            InlineKeyboardButton('✅ ارسال', callback_data='admin-confirm_broadcast'),
            InlineKeyboardButton('❌ لغو', callback_data='admin-cancel_broadcast')
            ]
        ]

        return self._create_list_inline_keyboard(buttons)
    def cancel_broadcast_button(self):
        buttons = [
            InlineKeyboardButton('❌ لغو', callback_data='admin-cancel_broadcast')
        ]

        return self._create_inline_keyboard(buttons)