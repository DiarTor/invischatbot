from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup,\
      InlineKeyboardButton, KeyboardButton
from telegram import CopyTextButton


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

    def account_buttons(self, is_bot_off=False):
        bot_status = 'خاموش😴' if is_bot_off else 'روشن 😁'
        buttons = [
            [
                InlineKeyboardButton('♻️ تغییر نام نمایشی', callback_data='change_nickname'),
            ],
            [
                InlineKeyboardButton(f'وضعیت ربات: {bot_status}', callback_data='change_bot_status')
            ]
        ]

        return self._create_list_inline_keyboard(buttons)

    def change_nickname_buttons(self):
        buttons = [
            InlineKeyboardButton('♻️ تغییر نام نمایشی', callback_data='change-nickname')
        ]
        return self._create_inline_keyboard(buttons)

    def sender_buttons(self, recipient_message_id: int, recipient_anon_id):
        # buttons = [
        #     InlineKeyboardButton('ویرایش پیام', callback_data=f'edit_message-{recipient_message_id}-{recipient_anon_id}', ),
        # ]
        buttons = [
            InlineKeyboardButton('🗑 حذف پیام',
                                 callback_data=f'delete_message-{recipient_message_id}-{recipient_anon_id}')
        ]
        return self._create_inline_keyboard(buttons)

    def recipient_buttons(self, sender_id, message_id=None):
        """
        :param sender_id: anonymous id
        :param message_id: message id
        :return: buttons
        """
        buttons = [
                [
                    InlineKeyboardButton('🛠 بیشتر...',
                                          callback_data=f'recipient_option-{sender_id}-{message_id}'),
                    InlineKeyboardButton('↪️ پاسخ',
                                          callback_data=f'reply-{sender_id}-{message_id}'),
                ]
        ]
        return self._create_list_inline_keyboard(buttons)

    def recipient_option_buttons(self, sender_id, message_id=None, is_seen=False, is_marked=False):
        """
        :param sender_id: anonymous id
        :param message_id: message id
        :param is_seen: if True, updates the 'seen' button to indicate it has already been seen
        :param is_marked: if True, updates the 'marked' button to indicate it has already been marked
        :return: buttons
        """
        buttons = [
            [
                InlineKeyboardButton('پیامتو دیدم 👀️' if not is_seen else 'قبلاً دیده شده ✅',
                                     callback_data=f'seen-{sender_id}-{message_id}' if not is_seen else 'placeholder'),
                InlineKeyboardButton('📌 علامت گذاری' if not is_marked else '📍 علامت گذاری شده',
                                     callback_data=f'mark-{sender_id}-{message_id}'),
            ],
            [
                InlineKeyboardButton('گزارش ⚠️', callback_data='report'),
                InlineKeyboardButton('بلاک 🚫', callback_data=f'block-{sender_id}-{message_id}')
            ],
            [
                InlineKeyboardButton('↩️ بازگشت', callback_data=f'return_to_recipient_buttons-{sender_id}-{message_id}'),
            ]
        ]
        return self._create_list_inline_keyboard(buttons)

    def block_confirmation_buttons(self, sender_id, message_id=None):
        """

        :param sender_id: anonymous id
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

    def blocklist_buttons(self, blocker_id: str, blocked_list: list):
        """ Block List InlineButtons
        :param blocker_id: blocker anonymous id
        :param blocked_list: the list of blocked anonymous ids
        :param message_id: message id
        """
        buttons = [
            [InlineKeyboardButton(text=str(blocked_id),
                                  callback_data=f'unblock-{blocker_id}-{blocked_id}'), ]
            for blocked_id in blocked_list
        ]
        return self._create_list_inline_keyboard(buttons)

    def unblock_confirmation_buttons(self, blocker_id: str, blocked_id: str):
        buttons = [
            [
                InlineKeyboardButton(f"میخوای {blocked_id} رو آنبلاک کنی؟", callback_data='placeholder')
            ],
            [InlineKeyboardButton('بله 👍', callback_data=f'unblock_confirm-{blocker_id}-{blocked_id}'),
             InlineKeyboardButton('خیر 👎', callback_data=f'unblock_cancel-{blocker_id}-placeholder')]]
        return self._create_list_inline_keyboard(buttons)

    def share_link_buttons(self, share_text: str, link: str = None):
        buttons = [
            [
                InlineKeyboardButton("کپی کردن لینک", copy_text=CopyTextButton(link)),
                InlineKeyboardButton("📤 اشتراک‌گذاری", switch_inline_query=share_text),
            ],
            [
                InlineKeyboardButton("🚫 ابطال لینک", callback_data='regenerate_link')
            ]
        ]

        return self._create_list_inline_keyboard(buttons)

    def inline_text_me_button(self, url: str):
        buttons = [
            InlineKeyboardButton("💬 ناشناس پیام بده!", url=url),
        ]
        return self._create_inline_keyboard(buttons)

    def force_join_buttons(self):
        buttons = [[
            InlineKeyboardButton('InvisChat Channel', url='t.me/invischats')
        ],
            [
                InlineKeyboardButton('✅ عضو شدم', callback_data='joined')
            ]]
        return self._create_list_inline_keyboard(buttons)

    def regenarate_link_buttons(self):
        buttons = [[
            InlineKeyboardButton("✅ بله مطمئنم", callback_data='confirm_regenerate_link'),
            InlineKeyboardButton("❌ نهههه", callback_data='cancel_regenerate_link'),
        ]]
        return self._create_list_inline_keyboard(buttons)