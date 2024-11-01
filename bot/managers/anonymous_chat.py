from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response


class ChatHandler:
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def anonymous_chat(self, msg: Message):
        user_chat = self._get_user_chat(msg.from_user.id)
        target_user_id = user_chat['chats'][0].get('target_user_id') if user_chat and user_chat['chats'] else None
        if user_chat and target_user_id and not self._is_user_blocked(msg.from_user.id, target_user_id):
            if user_chat.get("replying"):
                self._handle_reply(msg, user_chat)
            else:
                self._handle_forward(msg)
        else:
            # Notify the user they can't message the recipient
            self.bot.send_message(msg.chat.id, get_response('blocking.blocked_by_user'), parse_mode='Markdown')

    @staticmethod
    def _get_user_chat(user_id: int):
        """Retrieve the user's chat session."""
        return users_collection.find_one({"user_id": user_id})

    def _handle_reply(self, msg: Message, user_chat):
        """Handle the case where the user is replying to a message."""
        recipient_id = user_chat['reply_target_user_id']
        original_message_id = user_chat['reply_target_message_id']
        try:
            self.bot.send_message(
                recipient_id,
                get_response('texting.replying.recipient', msg.text),
                reply_to_message_id=original_message_id,
                parse_mode='Markdown',
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(
                    msg.from_user.id,
                    msg.id,
                    msg.text,
                ),
            )
        except ApiTelegramException:
            self.bot.send_message(msg.from_user.id, get_response('errors.bot_blocked'))
            self._reset_replying_state(msg.from_user.id)
            return

        # Notify the sender that their reply was sent
        self.bot.send_message(
            msg.chat.id,
            get_response('texting.replying.sent'),
            parse_mode='Markdown'
        )

        # Reset the replying state
        self._reset_replying_state(msg.from_user.id)

    def _handle_forward(self, msg: Message):
        """Handle forwarding of a message to the recipient."""
        active_chat = users_collection.find_one(
            {"user_id": msg.from_user.id, "chats.open": True, 'replying': False},
            {"chats.$": 1}  # Only return the open chat
        )

        if active_chat and 'chats' in active_chat:
            recipient_id = active_chat['chats'][0]['target_user_id']
            self._forward_message(msg, recipient_id)
        else:
            # Notify the sender that they are not currently in an anonymous chat
            self.bot.send_message(
                msg.chat.id,
                get_response('errors.no_active_chat'),
                parse_mode='Markdown'
            )

    def _forward_message(self, msg: Message, recipient_id: int):
        """Forward the message to the recipient."""
        try:
            self.bot.send_message(
                recipient_id,
                get_response('texting.sending.recipient', msg.text),
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(msg.from_user.id, msg.id, msg.text),
                parse_mode='Markdown'
            )

            # Notify the sender that their message was successfully sent
            self.bot.send_message(msg.chat.id, get_response('texting.sending.sent'), parse_mode='Markdown')

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
    def _reset_replying_state(user_id: int):
        """Reset the replying state for the user."""
        users_collection.update_one(
            {"user_id": user_id},
            {"$unset": {"replying": "", "reply_target_message_id": "", "reply_target_user_id": ""}}  # Clear reply state
        )
    @staticmethod
    def _is_user_blocked(sender_id: int, recipient_id: int) -> bool:
        """Check if the recipient has blocked the sender."""
        recipient_data = users_collection.find_one({"user_id": recipient_id}, {"blocked_users": 1})
        return sender_id in recipient_data.get('blocked_users', [])