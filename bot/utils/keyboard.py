from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


class KeyboardMarkupGenerator:
    """
    This Class have the functions to create KeyBoardMarkups
    """

    def _create_reply_keyboard(self, buttons):
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

    def _create_inline_keyboard(self, buttons):
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
    def _create_list_inline_keyboard(self, buttons):
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

    def recipient_buttons(self, sender_id, message_id=None, message_text=None):
        buttons = [InlineKeyboardButton('پاسخ ↪️', callback_data=f'reply-{sender_id}-{message_id}'),
                   InlineKeyboardButton('بلاک 🚫', callback_data=f'block-{sender_id}-{message_text}-{message_id}'), ]
        return self._create_inline_keyboard(buttons)

    def block_confirmation_buttons(self, sender_id, message_text=None, message_id=None):
        buttons = [InlineKeyboardButton('بله 👍', callback_data=f'block_confirm-{sender_id}-{message_id}'),
                   InlineKeyboardButton('خیر 👎', callback_data=f'block_cancel-{sender_id}-{message_text}-{message_id}')]
        return self._create_inline_keyboard(buttons)

    def blocklist_buttons(self, blocker_id: int, blocked_list: list, message_id=None):
        buttons = [
            [InlineKeyboardButton(text=str(blocked_id),
                                  callback_data=f'unblock-{blocker_id}-{blocked_id}-{message_id}'), ]
            for blocked_id in blocked_list
        ]
        return self._create_list_inline_keyboard(buttons)

    def unblock_confirmation_buttons(self, blocker_id: int, blocked_id: int, message_id=None):
        buttons = [
            InlineKeyboardButton('بله 👍', callback_data=f'unblock_confirm-{blocker_id}-{blocked_id}-{message_id}'),
            InlineKeyboardButton('خیر 👎', callback_data=f'unblock_cancel-{blocker_id}-{message_id}')]
        return self._create_inline_keyboard(buttons)
