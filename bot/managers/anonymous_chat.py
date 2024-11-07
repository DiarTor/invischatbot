from telebot.apihelper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.managers.nickname import NicknameManager
from bot.utils.chats import reset_replying_state, close_existing_chats
from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


class ChatHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def anonymous_chat(self, msg: Message):
        user_chat = self._get_user_chat(msg.from_user.id)

        # Check if there is an active chat or reply target
        target_user_id = None
        if user_chat.get('awaiting_nickname', None):
            await NicknameManager(self.bot).save_nickname(msg)
            return
        if user_chat and 'chats' in user_chat:
            # Search for a chat where 'open' is True
            open_chat = next((chat for chat in user_chat['chats'] if chat.get('open')), None)
            if open_chat:
                target_user_id = open_chat.get('target_user_id')
            elif 'reply_target_user_id' in user_chat:
                target_user_id = user_chat.get('reply_target_user_id')
        # Only proceed if there is a valid target_user_id
        if user_chat and target_user_id:
            # Check if the target user has blocked the sender or vice versa
            target_user_id = users_collection.find_one({'user_id': target_user_id}).get('id')
            if not self._is_user_blocked(user_chat['id'], target_user_id):
                if user_chat.get("replying"):
                    await self._handle_reply(msg, user_chat)
                else:
                    await self._handle_forward(msg)
            else:
                # If blocked, notify the sender they can't message the recipient
                close_existing_chats(msg.from_user.id)
                reset_replying_state(msg.from_user.id)
                await self.bot.send_message(msg.chat.id, get_response('blocking.blocked_by_user'),
                                            parse_mode='Markdown')
        else:
            # Notify the user they are not in an active chat
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'), parse_mode='Markdown')

    @staticmethod
    def _get_user_chat(user_id: int):
        """Retrieve the user's chat session."""
        return users_collection.find_one({"user_id": user_id})

    async def _handle_reply(self, msg: Message, user_chat):
        """Handle the case where the user is replying to a message."""
        recipient_bot_id = user_chat['reply_target_user_id']
        original_message_id = user_chat['reply_target_message_id']
        recipient_id = users_collection.find_one({"id": recipient_bot_id})['user_id']
        try:
            await self.bot.send_message(
                recipient_id,
                get_response('texting.replying.recipient', msg.text, user_chat['id']),
                reply_to_message_id=original_message_id,
                parse_mode='Markdown',
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(
                    user_chat['id'],
                    msg.id,
                    msg.text,
                ),
            )
        except ApiTelegramException:
            reset_replying_state(msg.from_user.id)
            await self.bot.send_message(msg.from_user.id, get_response('errors.bot_blocked'))
            return

        # Notify the sender that their reply was sent
        await self.bot.send_message(
            msg.chat.id,
            get_response('texting.replying.sent'),
            parse_mode='Markdown'
        )

        # Reset the replying state
        reset_replying_state(msg.from_user.id)

    async def _handle_forward(self, msg: Message):
        """Handle forwarding of a message to the recipient."""
        active_chat = users_collection.find_one(
            {"user_id": msg.from_user.id, "chats.open": True, 'replying': False},
            {"chats.$": 1}  # Only return the open chat
        )

        if active_chat and 'chats' in active_chat:
            recipient_id = active_chat['chats'][0]['target_user_id']
            await self._forward_message(msg, recipient_id)
        else:
            # Notify the sender that they are not currently in an anonymous chat
            await self.bot.send_message(
                msg.chat.id,
                get_response('errors.no_active_chat'),
                parse_mode='Markdown'
            )

    async def _forward_message(self, msg: Message, recipient_id: int):
        """Forward the message to the recipient."""
        user_bot_id = users_collection.find_one({"user_id": msg.from_user.id})['id']
        try:
            await self.bot.send_message(
                recipient_id,
                get_response('texting.sending.recipient', msg.text, user_bot_id),
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(user_bot_id, msg.id, msg.text),
                parse_mode='Markdown'
            )

            # Notify the sender that their message was successfully sent
            await self.bot.send_message(msg.chat.id, get_response('texting.sending.sent'), parse_mode='Markdown')

            # Close the active chat
            users_collection.update_one(
                {"user_id": msg.from_user.id, "chats.target_user_id": recipient_id, "chats.open": True},
                {"$set": {"chats.$.open": False}}
            )
        except ApiTelegramException:
            self._handle_bot_blocked(msg, recipient_id)

    def _handle_bot_blocked(self, msg: Message, recipient_id: int):
        """Handle the case where the bot is blocked by the recipient."""
        self.bot.send_message(msg.chat.id, get_response('errors.bot_blocked'))
        users_collection.update_one(
            {"user_id": msg.from_user.id, "chats.target_user_id": recipient_id, "chats.open": True},
            {"$set": {"chats.$.open": False}}
        )

    @staticmethod
    def _is_user_blocked(sender_id: int, recipient_id: int) -> bool:
        """Check if the recipient has blocked the sender."""
        sender_data = users_collection.find_one({"id": sender_id})
        recipient_data = users_collection.find_one({"id": recipient_id})

        # Check if sender_id is in the recipient's blocked_users list
        return sender_data['id'] in recipient_data['blocklist'] or recipient_data['id'] in sender_data['blocklist']
