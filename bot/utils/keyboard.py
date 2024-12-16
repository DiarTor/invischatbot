from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton


class KeyboardMarkupGenerator:
    """
    This Class have the functions to create KeyBoardMarkups
    """

    @staticmethod
    def _create_reply_keyboard(buttons):
        """
        Create ReplyKeyboardMarkup from list of buttons
        :param buttons:
        list of buttons (KeyboardButton)
        :return:
        ReplyKeyboardMarkup object
        """

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for row in buttons:
            markup.row(*row)
        return markup

    @staticmethod
    def _create_inline_keyboard(buttons):
        """
        Create InlineKeyboardMarkup from list of buttons
        :param buttons:
        list of buttons (InlineKeyboardButton)
        :return:
        InlineKeyboardMarkup object
        """

        markup = InlineKeyboardMarkup()
        for row in buttons:
            markup.row(row)
        return markup

    @staticmethod
    def _create_list_inline_keyboard(buttons):
        """
                Create InlineKeyboardMarkup list from list of buttons
                :param buttons:
                list of buttons (InlineKeyboardButton)
                :return:
                InlineKeyboardMarkup object
                """

        markup = InlineKeyboardMarkup()
        for row in buttons:
            markup.row(*row)
        return markup

    def main_buttons(self):
        buttons = [[KeyboardButton('🔗 لینک ناشناس من'), ],
                   [KeyboardButton('🚫 بلاک لیست'), KeyboardButton('👤 حساب کاربری')],
                   [KeyboardButton('🛠️ پشتیبانی'), KeyboardButton('📖 راهنما')],
                   ]

        return self._create_reply_keyboard(buttons)

    def cancel_buttons(self):
        buttons = [[KeyboardButton('⬅️ انصراف')]]

        return self._create_reply_keyboard(buttons)

    def cancel_changing_nickname(self):
        buttons = [InlineKeyboardButton('⬅️ بازگشت', callback_data='cancel-changing_nickname')]

        return self._create_inline_keyboard(buttons)

    def account_buttons(self):
        buttons = [InlineKeyboardButton('♻️ تغییر نام نمایشی', callback_data=f'change-nickname')]

        return self._create_inline_keyboard(buttons)

    def recipient_buttons(self, sender_id, message_id=None, seen=False):
        """
        :param sender_id: anny id
        :param message_id: message id
        :param seen: if True, updates the 'seen' button to indicate it has already been seen
        :return: buttons
        """
        buttons = [
            [
                InlineKeyboardButton('دیدم 👀️' if not seen else 'قبلاً دیده شده ✅',
                                     callback_data=f'seen-{sender_id}-{message_id}' if not seen else 'placeholder'),
                InlineKeyboardButton('پاسخ ↪️', callback_data=f'reply-{sender_id}-{message_id}'),
            ],
            [
                InlineKeyboardButton('گزارش ⚠️', callback_data='report'),
                InlineKeyboardButton('بلاک 🚫', callback_data=f'block-{sender_id}-{message_id}')
            ]
        ]
        return self._create_list_inline_keyboard(buttons)

    def block_confirmation_buttons(self, sender_id, message_id=None):
        """

        :param sender_id: anny id
        :param message_id:
        :return:
        """
        buttons = [
            [
                InlineKeyboardButton("میخوای طرفو بلاک کنی ؟", callback_data='placeholder')
            ],
            [
                InlineKeyboardButton('بله 👍', callback_data=f'block_confirm-{sender_id}-{message_id}'),
                InlineKeyboardButton('خیر 👎', callback_data=f'block_cancel-{sender_id}-{message_id}'),
            ]
        ]
        return self._create_list_inline_keyboard(buttons)

    def blocked_buttons(self):
        buttons = [InlineKeyboardButton('✅ کاربر بلاک شد.', callback_data='placeholder')]
        return self._create_inline_keyboard(buttons)

    def blocklist_buttons(self, blocker_id: str, blocked_list: list, message_id=None):
        """ Block List InlineButtons
        :param blocker_id: blocker anny id
        :param blocked_list: the list of blocked anny ids
        :param message_id: message id
        """
        buttons = [
            [InlineKeyboardButton(text=str(blocked_id),
                                  callback_data=f'unblock-{blocker_id}-{blocked_id}-{message_id}'), ]
            for blocked_id in blocked_list
        ]
        return self._create_list_inline_keyboard(buttons)

    def unblock_confirmation_buttons(self, blocker_id: str, blocked_id: str):
        buttons = [
            [
                InlineKeyboardButton(f"میخوای {blocked_id} رو آنبلاک کنی؟", callback_data='placeholder')
            ],
            [InlineKeyboardButton('بله 👍', callback_data=f'unblock_confirm-{blocker_id}-{blocked_id}'),
             InlineKeyboardButton('خیر 👎', callback_data=f'unblock_cancel-{blocker_id}')]]
        return self._create_list_inline_keyboard(buttons)
