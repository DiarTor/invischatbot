from decouple import config
from telebot.apihelper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager
from bot.managers.link import LinkManager
from bot.managers.start import StartBot
from bot.managers.support import SupportManager
from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.user_data import reset_replying_state, get_user, is_user_blocked, close_existing_chats


class ChatHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.current_version = config('VERSION', cast=float)

    async def anonymous_chat(self, msg: Message):
        """Main method to handle anonymous chat with support for different media types."""
        self.msg = msg
        user_chat = get_user(self.msg.chat.id)

        if not user_chat:
            await self.bot.reply_to(msg, get_response('errors.restart_required'))
            return

        user_version = user_chat.get('version', 0.0)
        if user_version != self.current_version:
            await self._handle_version_mismatch(msg)
            return

        # Handle commands from the keyboard
        keyboard_commands = {
            "⬅️ انصراف": self.handle_cancel,
            "🔗 لینک ناشناس من": self.handle_link,
            "🚫 بلاک لیست": self.handle_blocklist,
            '🛠️ پشتیبانی': self.handle_support,
            '📖 راهنما': self.handle_guide,
            '👤 حساب کاربری': self.handle_account
        }

        if msg.text in keyboard_commands:
            await keyboard_commands[msg.text]()
            return

        # Handle the chat message
        await self._handle_media(msg)

    async def _handle_version_mismatch(self, msg: Message):
        """Handle version mismatch by prompting a restart and updating the version."""
        users_collection.update_one(
            {'user_id': msg.from_user.id},
            {'$set': {'version': self.current_version}}
        )
        await StartBot(self.bot).start(msg)

    async def _handle_media(self, msg: Message):
        """Dispatch the handling of media based on the message type."""
        if msg.text:
            await self._handle_text(msg)
        elif msg.sticker:
            await self._handle_sticker(msg)
        elif msg.photo:
            await self._handle_photo(msg)
        elif msg.video:
            await self._handle_video(msg)
        elif msg.audio:
            await self._handle_audio(msg)
        elif msg.document:
            await self._handle_document(msg)
        else:
            await self.bot.send_message(msg.chat.id, get_response('errors.unknown_media'))

    async def _handle_text(self, msg: Message):
        """Handle text messages."""
        await self._process_chat(msg)

    async def _handle_sticker(self, msg: Message):
        """Handle sticker messages."""
        await self._process_chat(msg, is_sticker=True)

    async def _handle_photo(self, msg: Message):
        """Handle photo messages."""
        await self._process_chat(msg, is_photo=True)

    async def _handle_video(self, msg: Message):
        """Handle video messages."""
        await self._process_chat(msg, is_video=True)

    async def _handle_audio(self, msg: Message):
        """Handle audio messages."""
        await self._process_chat(msg, is_audio=True)

    async def _handle_document(self, msg: Message):
        """Handle document messages."""
        await self._process_chat(msg, is_document=True)

    async def _process_chat(self, msg: Message, **kwargs):
        """Process the chat based on the type of message."""
        user_chat = get_user(msg.from_user.id)
        open_chat = next((chat for chat in user_chat.get('chats', []) if chat.get('open')), None)
        if not user_chat.get('replying'):
            if open_chat:
                target_user_id = open_chat.get('target_user_id')
                if not is_user_blocked(user_chat.get('id'), target_user_id):
                    await self._forward_media(msg, target_user_id, **kwargs)
                else:
                    close_existing_chats(user_chat.get('user_id'))
                    await self.bot.send_message(msg.chat.id, get_response('blocking.blocked_by_user'),
                                                reply_markup=KeyboardMarkupGenerator().main_buttons())
            else:
                await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
        else:
            await self._handle_reply(msg, user_chat)

    async def _forward_media(self, msg: Message, recipient_id: int, **kwargs):
        sender_anny_id = get_user(msg.chat.id).get('id')
        caption = msg.caption if msg.caption else ""
        """Forward media to the recipient based on message type."""
        try:
            if kwargs.get('is_sticker'):
                await self.bot.send_message(recipient_id, get_response("texting.sending.sticker.recipient",
                                                                       sender_anny_id, ),
                                            parse_mode='Markdown',
                                            reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_anny_id,
                                                                                                     msg.id))
                await self.bot.send_sticker(recipient_id, msg.sticker.file_id)
            elif kwargs.get('is_photo'):
                await self.bot.send_photo(recipient_id, msg.photo[-1].file_id,
                                          caption=get_response('texting.sending.photo.recipient',
                                                               caption, sender_anny_id),
                                          parse_mode='Markdown')
            elif kwargs.get('is_video'):
                await self.bot.send_video(recipient_id, msg.video.file_id)
            elif kwargs.get('is_audio'):
                await self.bot.send_audio(recipient_id, msg.audio.file_id)
            elif kwargs.get('is_document'):
                await self.bot.send_document(recipient_id, msg.document.file_id)
            else:
                await self.bot.send_message(recipient_id, get_response("texting.sending.text.recipient", msg.text,
                                                                       get_user(msg.chat.id).get('id')),
                                            parse_mode='Markdown',
                                            reply_markup=KeyboardMarkupGenerator().recipient_buttons(
                                                get_user(msg.chat.id).get('id'), msg.id, msg.text))

            # After sending, update the chat state (if applicable)
            close_existing_chats(msg.chat.id)
            await self.bot.send_message(msg.chat.id, get_response('texting.sending.text.sent'), parse_mode='Markdown',
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())
        except ApiTelegramException:
            self._handle_bot_blocked(msg)

    async def _handle_reply(self, msg: Message, user_chat):
        """Handle replies to messages."""
        recipient_id, original_message_id = user_chat['reply_target_user_id'], user_chat['reply_target_message_id']
        recipient_user = users_collection.find_one({"id": recipient_id})

        if recipient_user:
            if not is_user_blocked(user_chat.get("id"), recipient_user.get('user_id')):
                try:
                    await self._send_reply(msg, recipient_user['user_id'], original_message_id, user_chat['id'])
                except ApiTelegramException:
                    self._handle_bot_blocked(msg)
                    return
            else:
                reset_replying_state(msg.chat.id)
                await self.bot.send_message(msg.chat.id, get_response('blocking.blocked_by_user'),
                                            reply_markup=KeyboardMarkupGenerator().main_buttons())
                return
            await self.bot.send_message(
                msg.chat.id, get_response('texting.replying.sent'), parse_mode='Markdown',
                reply_markup=KeyboardMarkupGenerator().main_buttons())
            reset_replying_state(msg.from_user.id)

    async def handle_link(self):
        await LinkManager(self.bot).link(self.msg)

    async def handle_blocklist(self):
        await BlockUserManager(self.bot).block_list(self.msg)

    async def handle_cancel(self):
        await self.cancel_chat_or_reply(self.msg)

    async def handle_support(self):
        await SupportManager(self.bot).support(self.msg)

    async def handle_guide(self):
        await SupportManager(self.bot).guide(self.msg)

    async def handle_account(self):
        await AccountManager(self.bot).account(self.msg)

    async def cancel_chat_or_reply(self, msg: Message):
        user_chat = get_user(msg.from_user.id)
        open_chat = next((chat for chat in user_chat.get('chats', []) if chat.get('open')), None)

        if user_chat.get("replying"):
            reset_replying_state(msg.from_user.id)
            await self.bot.send_message(
                msg.chat.id, get_response('texting.replying.cancelled'), parse_mode='Markdown',
                reply_markup=KeyboardMarkupGenerator().main_buttons()
            )
        elif open_chat:
            self._update_chat_field(msg.from_user.id, "chats.$.open", False,
                                    {"user_id": msg.from_user.id, "chats.open": True})
            await self.bot.send_message(
                msg.chat.id, get_response('texting.sending.cancelled'), parse_mode='Markdown',
                reply_markup=KeyboardMarkupGenerator().main_buttons()
            )
        elif user_chat.get('awaiting_nickname'):
            self._update_user_field(msg.from_user.id, "awaiting_nickname", False)
            await self.bot.send_message(msg.from_user.id, get_response('nickname.cancelled'),
                                        parse_mode='Markdown',
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())
        else:
            await self.bot.send_message(
                msg.chat.id, get_response('errors.no_cancel'), parse_mode='Markdown'
            )

    async def _send_reply(self, msg: Message, recipient_id, original_message_id, sender_id):
        await self.bot.send_message(
            recipient_id,
            get_response('texting.replying.recipient', msg.text, sender_id),
            reply_to_message_id=original_message_id,
            parse_mode='Markdown',
            reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_id, msg.id, msg.text)
        )

    async def _handle_forward(self, msg: Message):
        active_chat = self._get_active_chat(msg.from_user.id)

        if active_chat:
            recipient_id = active_chat['target_user_id']
            await self._forward_message(msg, recipient_id)
        else:
            await self.bot.send_message(
                msg.chat.id, get_response('errors.no_active_chat'), parse_mode='Markdown'
            )

    async def _forward_message(self, msg: Message, recipient_id: int):
        user_bot_id = users_collection.find_one({"user_id": msg.from_user.id})['id']
        try:
            await self.bot.send_message(
                recipient_id,
                get_response('texting.sending.text.recipient', msg.text, user_bot_id),
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(user_bot_id, msg.id, msg.text),
                parse_mode='Markdown'
            )
            await self.bot.send_message(
                msg.chat.id, get_response('texting.sending.text.sent'), parse_mode='Markdown',
                reply_markup=KeyboardMarkupGenerator().main_buttons()
            )
            self._update_chat_field(msg.from_user.id, "chats.$.open", False,
                                    {"user_id": msg.from_user.id, "chats.target_user_id": recipient_id,
                                     "chats.open": True})
        except ApiTelegramException:
            self._handle_bot_blocked(msg)

    @staticmethod
    def _get_active_chat(user_id):
        return users_collection.find_one(
            {"user_id": user_id, "chats.open": True, 'replying': False},
            {"chats.$": 1}
        ).get('chats', [None])[0]

    def _handle_bot_blocked(self, msg: Message):
        self.bot.send_message(msg.chat.id, get_response('errors.bot_blocked'))

    @staticmethod
    def _update_user_field(user_id, field, value):
        users_collection.update_one({"user_id": user_id}, {"$set": {field: value}})

    @staticmethod
    def _update_chat_field(user_id, field, value, query=None):
        if not query:
            query = {"user_id": user_id, "chats.open": True}
        users_collection.update_one(query, {"$set": {field: value}})
