"""Callback handler for processing user interactions with the bot."""
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InputTextMessageContent,\
      InlineQueryResultArticle, InlineQuery
from bot.common.chat_utils import close_chats, add_seen_message, get_seen_status
from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager
from bot.managers.nickname import NicknameManager
from bot.managers.settings import SettingsManager
from bot.managers.start import StartBot
from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.database_utils import fetch_user_data_by_id, update_user_fields,\
      get_user_id, get_user_anon_id
from bot.common.user import is_subscribed_to_channel, is_bot_status_off
from bot.common.utils import generate_anon_link
from bot.admin.callback import AdminCallbackHandler
from bot.common.database_utils import is_user_banned


class CallbackHandler:
    """CallbackHandler is a class responsible for handling various callback queries &
    inline queries received by the bot.
    It processes user interactions and executes the appropriate actions based 
    on the callback data."""

    def __init__(self, bot: AsyncTeleBot):
        """Initialize the CallbackHandler with the bot instance."""
        self.bot = bot
        self.callback_handlers = {
            'reply': self._process_reply_callback,
            'joined': self._process_joined_channel,
            'delete_message': self._process_delete_message_callback,
            'seen': self._process_seen_callback,
            'block': self._process_block_callback, #naming problems
            'block_cancel': self._process_block_callback, #naming problems
            'block_confirm': self._process_block_callback, #naming problems
            'report': self._process_report_callback,
            'mark': self._process_mark_message,
            'unblock': self._process_unblock_callback,
            'unblock_cancel': self._process_unblock_callback,
            'unblock_confirm': self._process_unblock_callback,
            'change_nickname': self._process_change_nickname,
            'change_bot_status': self._process_change_bot_status,
            'cancel': self._process_cancel,
            'admin': self._process_admin_callback,
        }
        self.keyboard = KeyboardMarkupGenerator()
        self.blocker = BlockUserManager(self.bot)

    async def handle_callback(self, callback: CallbackQuery):
        """Main method to handle callbacks from the user."""
        callback_data = callback.data

        if is_user_banned(callback.from_user.id):
            await self._send_ban_message(callback)
            return

        # Extract the action type from the callback data
        action = callback_data.split('-')[0]

        # Find and execute the corresponding handler
        handler = self.callback_handlers.get(action)
        if handler:
            await handler(callback)
        else:
            await self.bot.answer_callback_query(callback.id,
                                                get_response('errors.unknown_action'),
                                                show_alert=True)

        await self.bot.answer_callback_query(callback.id)

    async def handle_inline_query(self, inline: InlineQuery):
        """Handle inline queries."""
        user_id = inline.from_user.id
        text = inline.query.strip() or "حرفتو ناشناس بهم بزن 😉"  # Default text if empty
        link = generate_anon_link(get_user_anon_id(user_id))

        content = InputTextMessageContent(f"{text}")
        result = InlineQueryResultArticle(
            id=inline.id,
            title="متن خودت رو بنویس",
            description=text,
            input_message_content=content,
            thumbnail_url='https://s8.uupload.ir/files/photo_2024-10-20_02-07-59_h3tq.jpg',
            reply_markup=self.keyboard.inline_text_me_button(link)
        )

        await self.bot.answer_inline_query(inline.id, results=[result])

    async def _send_ban_message(self, callback: CallbackQuery):
        """Send a message to banned users."""
        await self.bot.send_message(
            callback.message.chat.id,
            get_response('account.ban.banned'),
            reply_markup=self.keyboard.main_buttons()
        )

    async def _process_reply_callback(self, callback: CallbackQuery):
        """Process the reply callback and set the replying state."""
        _, sender_anon_id, message_id = callback.data.split('-')
        sender_user_id = get_user_id(sender_anon_id)
        if await self._check_bot_status(callback, sender_user_id):
            return

        close_chats(callback.from_user.id)
        self._set_replying_state(callback.from_user.id, message_id, sender_anon_id)

        await self.bot.send_message(
            callback.from_user.id,
            get_response('texting.replying.send'),
            reply_to_message_id=callback.message.id,
            parse_mode='Markdown',
            reply_markup=self.keyboard.cancel_buttons()
        )

    async def _process_seen_callback(self, callback: CallbackQuery):
        """Process the seen callback."""
        sender_anon_id, message_id = callback.data.split('-')[1:]
        sender_id = get_user_id(sender_anon_id)

        if await self._check_bot_status(callback, sender_id):
            return

        add_seen_message(callback.from_user.id, int(message_id))
        await self.bot.send_message(
            chat_id=sender_id,
            reply_to_message_id=message_id,
            text=get_response('texting.seen.recipient')
        )
        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.recipient_buttons(sender_anon_id, message_id, True)
        )
        await self.bot.answer_callback_query(callback.id, get_response('texting.seen.sent'))

    async def _process_block_callback(self, callback: CallbackQuery):
        """Process the block callback."""
        action, sender_id, message_id = callback.data.split('-')

        if action == 'block':
            if await self._validate_block_action(callback, sender_id):
                return
            await self.bot.edit_message_reply_markup(
                callback.message.chat.id,
                callback.message.id,
                reply_markup=self.keyboard.block_confirmation_buttons(sender_id, message_id)
            )
        elif action == 'block_confirm':
            await self.blocker.block_user(callback.message.chat.id, sender_id, callback)
        elif action == 'block_cancel':
            await self.blocker.cancel_block(callback, message_id, sender_id)

    async def _process_unblock_callback(self, callback: CallbackQuery):
        """Process the unblock callback."""
        action, blocker_id, blocked_id = callback.data.split('-')

        if action == 'unblock':
            await self.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                reply_markup=self.keyboard.unblock_confirmation_buttons(blocker_id, blocked_id)
            )
        elif action == 'unblock_confirm':
            blocker_anon_id = users_collection.find_one({"user_id": callback.message.chat.id})['id']
            await self.blocker.unblock_user(blocker_anon_id, blocked_id, callback)
        elif action == 'unblock_cancel':
            blocker_anon_id = users_collection.find_one({"user_id": callback.message.chat.id})['id']
            await self.blocker.cancel_unblock_user(blocker_anon_id, callback.message.id)

    async def _process_delete_message_callback(self, callback: CallbackQuery):
        """Process the delete message callback"""
        recipient_message_id, recipient_anon_id = callback.data.split('-')
        await self.bot.delete_message(get_user_id(recipient_anon_id), int(recipient_message_id))
        await self.bot.edit_message_text(get_response('texting.tools.delete.deleted'),
                                         callback.message.chat.id,
                                         callback.message.id, parse_mode='Markdown')
    async def _process_report_callback(self, callback: CallbackQuery):
        """Process the report callback"""
        await self.bot.answer_callback_query(callback.id,
                                            get_response('reporting.send'), show_alert=True)

    async def _process_change_nickname(self, callback: CallbackQuery):
        """Process the change nickname callback."""
        response = NicknameManager(self.bot).get_set_nickname_response(callback.message)
        await self.bot.edit_message_text(
            response,
            callback.message.chat.id,
            callback.message.id,
            parse_mode='Markdown',
            reply_markup=self.keyboard.cancel_changing_nickname()
        )

    async def _process_cancel(self, callback: CallbackQuery):
        """Process the cancel callback."""
        _, task = callback.data.split('-')
        if task == "changing_nickname":
            await update_user_fields(callback.from_user.id, 'awaiting_nickname', False)
            await self.bot.edit_message_text(
                AccountManager(self.bot).get_account_response(callback.message),
                callback.from_user.id,
                callback.message.id,
                parse_mode='Markdown',
                reply_markup=self.keyboard.account_buttons()
            )

    async def _process_change_bot_status(self, callback: CallbackQuery):
        """Process the change bot status callback."""
        await SettingsManager(self.bot).change_bot_status(callback)

    async def _process_mark_message(self, callback: CallbackQuery):
        """Process the mark message callback."""
        sender_anon_id, message_id = callback.data.split('-')[1:]
        seen = get_seen_status(user_id=callback.message.chat.id, message_id=callback.message.id)

        original_text, is_caption = self._get_message_text_or_caption(callback)
        if not original_text:
            await self.bot.answer_callback_query(callback.id, "Cannot mark this message.")
            return

        new_text, marked = self._toggle_mark(original_text)
        await self._edit_message(callback, new_text, sender_anon_id,
                                  message_id, seen, marked, is_caption)

    async def _process_joined_channel(self, callback: CallbackQuery):
        """Process the joined channel callback."""
        if not await is_subscribed_to_channel(self.bot, callback.message.chat.id):
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('ad.not_joined'), show_alert=True)
            return
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)
        await StartBot(self.bot).start(callback.message)

    async def _process_admin_callback(self, callback: CallbackQuery):
        """Delegate admin-related callbacks to the AdminCallbackHandler."""
        await AdminCallbackHandler(self.bot).handle_callback(callback)

    @staticmethod
    def _set_replying_state(user_id: int, message_id: str, sender_anon_id: str):
        """Set the replying state in the database."""
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "replying": True,
                    "reply_target_message_id": message_id,
                    "reply_target_user_id": str(sender_anon_id),
                },
            }
        )

    @staticmethod
    def _get_message_text_or_caption(callback: CallbackQuery):
        """Get the text or caption of a message."""
        if callback.message.text:
            return callback.message.text, False
        elif callback.message.caption:
            return callback.message.caption, True
        return None, False

    @staticmethod
    def _toggle_mark(original_text: str):
        """Toggle the mark status of a message."""
        if "#️⃣ #mark" in original_text.strip():
            return original_text.replace("\n #️⃣ #mark", "").strip(), False
        return f"{original_text}\n #️⃣ #mark", True

    async def _edit_message(self, callback, new_text, sender_anon_id,
                            message_id, seen, marked, is_caption):
        """Edit the message text or caption."""
        if is_caption:
            await self.bot.edit_message_caption(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                caption=new_text,
                reply_markup=self.keyboard.recipient_buttons(sender_anon_id, message_id,
                                                             seen, marked)
            )
        else:
            await self.bot.edit_message_text(
                new_text,
                callback.message.chat.id,
                callback.message.id,
                reply_markup=self.keyboard.recipient_buttons(sender_anon_id, message_id,
                                                             seen, marked)
            )

    async def _check_bot_status(self, callback: CallbackQuery, sender_id: str):
        """Check if the bot status is off for the user or recipient."""
        if is_bot_status_off(callback.from_user.id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.self.off'),
                show_alert=True
            )
            return True
        if is_bot_status_off(sender_id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.recipient.off'),
                show_alert=True
            )
            return True
        return False

    async def _validate_block_action(self, callback: CallbackQuery, sender_id: str):
        """Validate block action to prevent blocking self or support."""
        if sender_id == fetch_user_data_by_id(callback.message.chat.id).get('id'):
            await self.bot.answer_callback_query(callback.id, get_response('blocking.self'))
            return True
        if sender_id == 'support':
            await self.bot.answer_callback_query(callback.id, get_response('blocking.support'))
            return True
        return False
