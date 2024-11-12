from telebot.apihelper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.managers.nickname import NicknameManager
from bot.utils.user_data import reset_replying_state
from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


class ChatHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def anonymous_chat(self, msg: Message):
        user_chat = self._get_user(msg.from_user.id)
        if not user_chat:
            await self.bot.reply_to(msg, get_response('errors.restart_required'))
            return

        if msg.text == "⬅️ انصراف":
            await self.cancel_chat_or_reply(msg)
            return

        open_chat = next((chat for chat in user_chat.get('chats', []) if chat.get('open')), None)

        if user_chat.get('awaiting_nickname'):
            if open_chat or user_chat.get('reply_target_user_id'):
                self._update_user_field(msg.from_user.id, "awaiting_nickname", False)
            else:
                await NicknameManager(self.bot).save_nickname(msg)
                return

        target_user_id = open_chat.get('target_user_id') if open_chat else user_chat.get('reply_target_user_id')

        if target_user_id and not self._is_user_blocked(user_chat.get('id'), target_user_id):
            if user_chat.get("replying"):
                await self._handle_reply(msg, user_chat)
            else:
                await self._handle_forward(msg)
        else:
            await self.bot.send_message(msg.from_user.id, get_response('errors.no_active_chat'))

    async def cancel_chat_or_reply(self, msg: Message):
        user_chat = self._get_user(msg.from_user.id)
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
            await self.bot.send_message(msg.from_user.id, get_response('texting.sending.cancelled'), parse_mode='Markdown',
                                  reply_markup=KeyboardMarkupGenerator().main_buttons())
        else:
            await self.bot.send_message(
                msg.chat.id, get_response('errors.no_cancel'), parse_mode='Markdown'
            )

    @staticmethod
    def _get_user(user_id: int):
        return users_collection.find_one({"user_id": user_id})

    async def _handle_reply(self, msg: Message, user_chat):
        recipient_id, original_message_id = user_chat['reply_target_user_id'], user_chat['reply_target_message_id']
        recipient_user = users_collection.find_one({"id": recipient_id})

        if recipient_user:
            try:
                await self._send_reply(msg, recipient_user['user_id'], original_message_id, user_chat['id'])
            except ApiTelegramException:
                self._handle_bot_blocked(msg)
                return

            await self.bot.send_message(
                msg.chat.id, get_response('texting.replying.sent'), parse_mode='Markdown'
            )
            reset_replying_state(msg.from_user.id)

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
                get_response('texting.sending.recipient', msg.text, user_bot_id),
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(user_bot_id, msg.id, msg.text),
                parse_mode='Markdown'
            )
            await self.bot.send_message(
                msg.chat.id, get_response('texting.sending.sent'), parse_mode='Markdown',
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

    @staticmethod
    def _is_user_blocked(sender_id: str, recipient_id: int) -> bool:
        sender_data = users_collection.find_one({"id": sender_id})
        recipient_data = users_collection.find_one({"user_id": recipient_id})

        return recipient_data and (
                sender_data['id'] in recipient_data.get('blocklist', []) or
                recipient_data['id'] in sender_data.get('blocklist', [])
        )
