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
        buttons = [[KeyboardButton('🕊 ارسال بدون لینک'), KeyboardButton('🔗 لینک ناشناس من'), ],
                   [KeyboardButton('🚫 بلاک لیست'), KeyboardButton('👤 حساب کاربری')],
                   [KeyboardButton('📖 راهنما')] #KeyboardButton('🛠️ پشتیبانی'), ,
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
                    InlineKeyboardButton('🎈 بیشتر...',
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
                InlineKeyboardButton('📌 علامت گذاری' if not is_marked else '📍 حذف علامت گذاری',
                                     callback_data=f'mark-{sender_id}-{message_id}'),
            ],
            [
                # InlineKeyboardButton('گزارش ⚠️', callback_data='report'),
                InlineKeyboardButton('بلاک 🚫', callback_data=f'block-{sender_id}-{message_id}'),
                InlineKeyboardButton('👍 ریاکشن ها', callback_data=f'reactions-{sender_id}-{message_id}')
            ],
            [
                InlineKeyboardButton('↩️ بازگشت', callback_data=f'return_to_recipient_buttons-{sender_id}-{message_id}'),
            ]
        ]
        return self._create_list_inline_keyboard(buttons)

    def reaction_buttons(self, sender_id, message_id=None, toggled_emoji='اگه قبلا ریاکشن دادین، همون مونده!'):
        """
        :param sender_id: anonymous id
        :param message_id: message id
        :return: buttons
        """
        buttons = [
            [
                InlineKeyboardButton('👍', callback_data=f'reaction-like-{sender_id}-{message_id}'),
                InlineKeyboardButton('👎', callback_data=f'reaction-dislike-{sender_id}-{message_id}'),
            ],
            [
                InlineKeyboardButton('❤️', callback_data=f'reaction-heart-{sender_id}-{message_id}'),
                InlineKeyboardButton('🔥', callback_data=f'reaction-fire-{sender_id}-{message_id}'),
                InlineKeyboardButton('😁', callback_data=f'reaction-smile-{sender_id}-{message_id}'),
                InlineKeyboardButton('🤣', callback_data=f'reaction-laugh-{sender_id}-{message_id}'),
            ],
            [
                InlineKeyboardButton('🙏', callback_data=f'reaction-thanks-{sender_id}-{message_id}'),
                InlineKeyboardButton('👏', callback_data=f'reaction-clap-{sender_id}-{message_id}'),
                InlineKeyboardButton('😢', callback_data=f'reaction-sad-{sender_id}-{message_id}'),
                InlineKeyboardButton('😭', callback_data=f'reaction-cry-{sender_id}-{message_id}'),
            ],
            [
                InlineKeyboardButton('😡', callback_data=f'reaction-angry-{sender_id}-{message_id}'),
                InlineKeyboardButton('🤔', callback_data=f'reaction-thinking-{sender_id}-{message_id}'),
                InlineKeyboardButton('🗿', callback_data=f'reaction-chad-{sender_id}-{message_id}'),
                InlineKeyboardButton('🌚', callback_data=f'reaction-moon-{sender_id}-{message_id}'),
            ],
            [
                InlineKeyboardButton('↩️ بازگشت', callback_data=f'return_to_recipient_option_buttons-{sender_id}-{message_id}')
            ]
        ]
        buttons += [[InlineKeyboardButton(f'ریاکشن فعلی: {toggled_emoji}', callback_data='placeholder')]]
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
                InlineKeyboardButton("🚫 ابطال لینک", callback_data='revoke_link')
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
        """Create buttons for regenerating the link."""
        buttons = [[
            InlineKeyboardButton("✅ بله مطمئنم", callback_data='confirm_revoke_link'),
            InlineKeyboardButton("❌ نهههه", callback_data='cancel_revoke_link'),
        ]]
        return self._create_list_inline_keyboard(buttons)

    def guide_buttons(self):
        """Create guide buttons for guide functionality."""
        buttons = [
            [
                InlineKeyboardButton("📞 پشتیبانی", callback_data='guide-support'),
                InlineKeyboardButton("❓ سوالات متداول", callback_data='guide-faq'),
            ],
        ]
        return self._create_list_inline_keyboard(buttons)

    def faq_buttons(self):
        """Create FAQ buttons for FAQ functionality."""
        buttons = [
            InlineKeyboardButton("🤔 این ربات چیه؟ و چیکار میکنه؟", callback_data='guide-faq-what_is_invischat'),
            InlineKeyboardButton("🛠️ چطور از ربات استفاده کنم؟", callback_data='guide-faq-how_to_use'),
            InlineKeyboardButton("🚨 چطور کاربر رو گزارش بدم؟", callback_data='guide-faq-how_to_report_user'),
            # InlineKeyboardButton("🔗 چطور به کاربر خاصی وصل بشم؟", callback_data='guide-faq-how_to_connect_to_speceific_user'),
            InlineKeyboardButton("🔙 صفحه راهنما", callback_data='guide-return_to_guide'),
        ]
        return self._create_inline_keyboard(buttons)
    def return_to_faq_buttons(self):
        """Create buttons to return to the FAQ main menu."""
        buttons = [
            InlineKeyboardButton("🔙 صفحه سوالات", callback_data='guide-faq')
        ]
        return self._create_inline_keyboard(buttons)
