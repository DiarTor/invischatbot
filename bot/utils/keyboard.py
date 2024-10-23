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

    def recipient_buttons(self, sender_id, message_id):
        buttons = [InlineKeyboardButton('پاسخ ↪️', callback_data=f'reply-{sender_id}-{message_id}')]
        return self._create_inline_keyboard(buttons)
