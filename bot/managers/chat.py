import asyncio

import pytz
from decouple import config
from jdatetime import datetime
from telebot.apihelper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.common.chat_utils import close_chats
from bot.common.database_utils import fetch_user_data_by_id, is_user_banned, update_user_fields, get_user_anon_id, get_user_id, \
    update_total_messages
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.threads import delete_message
from bot.common.user import is_bot_status_off
from bot.database.database import users_collection
from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager
from bot.managers.link import LinkManager
from bot.managers.nickname import NicknameManager
from bot.managers.start import StartBot
from bot.managers.support import SupportManager


class ChatHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.current_version = config('VERSION', cast=float)

    async def anonymous_chat(self, msg: Message):
        """Main method to handle anonymous chat with support for different media types."""
        self.msg = msg
        user_chat = fetch_user_data_by_id(self.msg.chat.id)

        if not user_chat:
            await StartBot(self.bot).start(msg)
            return

        user_version = user_chat.get('version', 0.0)
        if user_version != self.current_version:
            await self._handle_version_mismatch(msg)
            return
        if is_user_banned(user_chat.get('user_id')):
            await self.bot.send_message(msg.chat.id, get_response('account.ban.banned'),
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())
            return

        # if not await is_subscribed_to_channel(self.bot, self.msg.chat.id):
        #     await self.bot.send_message(self.msg.chat.id, get_response('ad.force_join'),
        #                                 reply_markup=KeyboardMarkupGenerator().force_join_buttons())
        #     return
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

    async def _handle_media(self, msg: Message):
        """Dispatch the handling of media based on the message type."""
        media_mapping = {
            "text": {"is_text": True},
            "sticker": {"is_sticker": True},
            "photo": {"is_photo": True},
            "video": {"is_video": True},
            "audio": {"is_audio": True},
            "document": {"is_document": True},
            "video_note": {"is_video_note": True},
            "voice": {"is_voice": True},
        }

        for media_type, kwargs in media_mapping.items():
            if getattr(msg, media_type, None):
                await self._process_chat(msg, **kwargs)
                return

        # Handle unknown media
        await self.bot.send_message(msg.chat.id, get_response("errors.unknown_media"))

    async def _process_chat(self, msg: Message, **kwargs):
        """Process the chat based on the type of message."""
        user_chat = fetch_user_data_by_id(msg.from_user.id)
        open_chat = next((chat for chat in user_chat.get('chats', []) if chat.get('open')), None)

        # Check if the user is in awaiting nickname state and trying to send a message, if so set the state to false
        # so the text they send serves as a message and doesn't set to their nickname.
        # this condition happens when someone is in awaiting nickname state and set their replying state to True or open a chat.
        if open_chat or user_chat.get('replying') and user_chat.get('awaiting_nickname'):
            users_collection.update_one({'user_id': msg.chat.id}, {'$set': {'awaiting_nickname': False}})
            user_chat = fetch_user_data_by_id(msg.chat.id)
        # Check if the user is in replying state, if so handle the text as reply message.
        if user_chat.get('replying'):
            await self._handle_reply(msg, user_chat)
            return
        # Check if the user is in awaiting nickname state, if so handle the text as nickname.
        if user_chat.get('awaiting_nickname'):
            await NicknameManager(self.bot).save_nickname(msg)
            return

        if msg.reply_to_message and msg.reply_to_message.id == user_chat.get('editing_prompt_message_id'):
            await self._handle_editing(msg, user_chat)
            return
        # Check if there is any open chat when the user sent the message
        if not open_chat:
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return

        # Check if the target user blocked the user
        target_user_id = open_chat.get('target_user_id')
        if await BlockUserManager.is_user_blocked(user_chat.get('id'), target_user_id):
            close_chats(user_chat.get('user_id'))
            await self.bot.send_message(msg.chat.id, get_response('blocking.blocked_by_user'),
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())
        # check if the target user changed the bot status to off
        if is_bot_status_off(target_user_id):
            close_chats(user_chat.get('user_id'))
            await self.bot.send_message(msg.chat.id, get_response('account.bot_status.recipient.off'),
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())

        # if everything is fine, forward the message
        await self._handle_forward(msg, target_user_id, **kwargs)

    async def _send_media(self, msg: Message, recipient_id: int, sender_anon_id: str, reply_to_message_id=None):
        """
        Send media based on its type.
        :param recipient_id: recipient user id.
        :param sender_anon_id: sender anonymous id.
        :param reply_to_message_id: reply message id.
        """
        global target_message
        caption = msg.caption if msg.caption else ""
        reply_markup = KeyboardMarkupGenerator().recipient_buttons(sender_anon_id, msg.id)
        base_kwargs = {
            "caption": get_response('texting.sending.text.recipient', message=caption, sender_anon_id=sender_anon_id),
            "parse_mode": 'Markdown',
            "reply_markup": reply_markup,
        }
        strict_kwargs = {
            "reply_markup": reply_markup,
        }
        if reply_to_message_id:
            base_kwargs["reply_to_message_id"] = reply_to_message_id
            strict_kwargs['reply_to_message_id'] = reply_to_message_id
        try:
            if msg.sticker:
                target_message = await self.bot.send_sticker(recipient_id, msg.sticker.file_id, **strict_kwargs)
            elif msg.photo:
                target_message = await self.bot.send_photo(recipient_id, msg.photo[-1].file_id, **base_kwargs)
            elif msg.video:
                target_message = await self.bot.send_video(recipient_id, msg.video.file_id, **base_kwargs)
            elif msg.voice:
                target_message = await self.bot.send_voice(recipient_id, msg.voice.file_id, **base_kwargs)
            elif msg.video_note:
                target_message = await self.bot.send_video_note(recipient_id, msg.video_note.file_id, **strict_kwargs)
            elif msg.audio:
                target_message = await self.bot.send_audio(recipient_id, msg.audio.file_id, **base_kwargs)
            elif msg.document:
                target_message = await self.bot.send_document(recipient_id, msg.document.file_id, **base_kwargs)
            else:  # Default to text
                target_message = await self.bot.send_message(
                    recipient_id, get_response("texting.sending.text.recipient", message=msg.text, sender_anon_id=sender_anon_id),
                    **strict_kwargs,
                )
                # await self.bot.send_message(
                #     msg.chat.id, get_response('texting.sending.text.sent'),
                #     parse_mode='Markdown'
                # )
            close_chats(msg.from_user.id)
            await self.bot.send_message(
                msg.chat.id, get_response('texting.sending.text.sent'),
                parse_mode='Markdown', reply_markup=KeyboardMarkupGenerator().main_buttons(),
                reply_to_message_id=msg.id
            )
            await update_total_messages(1)
            tools_message = await self.bot.send_message(msg.chat.id, get_response('texting.tools.announce'),
                                                        reply_markup=KeyboardMarkupGenerator().sender_buttons(
                                                            target_message.id,
                                                            get_user_anon_id(
                                                                recipient_id)),
                                                        reply_to_message_id=msg.id)
            asyncio.create_task(delete_message(self.bot, msg.chat.id, tools_message.id, minutes=0.09))
        except ApiTelegramException:
            self._handle_bot_blocked(msg)

    async def _handle_forward(self, msg: Message, recipient_id: int, **kwargs):
        """
        Forward media to a recipient.

        :param recipient_id: recipient user id.
        """
        sender_anon_id = fetch_user_data_by_id(msg.chat.id).get('id')
        await self._send_media(msg, recipient_id, sender_anon_id)

    async def _handle_reply(self, msg: Message, user_chat):
        """Handle replies to a message."""
        recipient_id, original_message_id = user_chat['reply_target_user_id'], user_chat['reply_target_message_id']
        recipient_user = users_collection.find_one({"id": recipient_id})

        if not recipient_user:
            close_chats(msg.chat.id, True)
            await self.bot.send_message(
                msg.chat.id, get_response('errors.user_not_found'),
                reply_markup=KeyboardMarkupGenerator().main_buttons()
            )
            return

        if await BlockUserManager.is_user_blocked(user_chat.get("id"), recipient_user.get('user_id')):
            close_chats(msg.chat.id, True)
            await self.bot.send_message(
                msg.chat.id, get_response('blocking.blocked_by_user'),
                reply_markup=KeyboardMarkupGenerator().main_buttons()
            )
            return

        sender_anon_id = user_chat.get('id')
        await self._send_media(msg, recipient_user['user_id'], sender_anon_id, reply_to_message_id=original_message_id)
        close_chats(msg.from_user.id, True)

    async def _handle_editing(self, msg: Message, user_chat):
        """Handle editing of a message."""
        target_id = get_user_id(user_chat.get('editing_target_anon_id'))
        try:
            jdate = datetime.now(pytz.timezone('Asia/Tehran')).strftime('%H:%M %Y/%m/%d')
            # Edit the target message
            await self.bot.edit_message_text(
                chat_id=target_id,
                message_id=int(user_chat.get('editing_target_message_id')),
                text=get_response('texting.tools.editing.recipient', message=msg.text, anon_id=get_user_anon_id(msg.chat.id), edited_at=jdate),
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(get_user_anon_id(msg.chat.id), msg.id)
            )

            # Confirm the edit
            await self.bot.send_message(
                chat_id=msg.chat.id,
                text=get_response('texting.tools.editing.sent'),
                reply_markup=KeyboardMarkupGenerator().main_buttons(),
                reply_to_message_id=msg.id
            )

            # Clear the editing-related fields
            update_user_fields(msg.chat.id, {
                "editing_target_message_id": int(),
                "editing_prompt_message_id": int()
            })

        except Exception as e:
            print(f"Unable to edit the message. Error: {e}")

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
        user_chat = fetch_user_data_by_id(msg.from_user.id)
        open_chat = next((chat for chat in user_chat.get('chats', []) if chat.get('open')), None)

        if user_chat.get("replying"):
            close_chats(msg.from_user.id, True)
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

    async def _handle_version_mismatch(self, msg: Message):
        """Handle version mismatch by prompting a restart and updating the version."""
        users_collection.update_one(
            {'user_id': msg.from_user.id},
            {'$set': {'version': self.current_version}}
        )
        await StartBot(self.bot).start(msg)

    def _handle_bot_blocked(self, msg: Message):
        close_chats(msg.chat.id, True)
        self.bot.send_message(msg.chat.id, get_response('errors.bot_blocked'),
                              reply_markup=KeyboardMarkupGenerator().main_buttons())

    @staticmethod
    def _update_user_field(user_id, field, value):
        users_collection.update_one({"user_id": user_id}, {"$set": {field: value}})

    @staticmethod
    def _update_chat_field(user_id, field, value, query=None):
        if not query:
            query = {"user_id": user_id, "chats.open": True}
        users_collection.update_one(query, {"$set": {field: value}})
