from telebot import TeleBot
from telebot.types import CallbackQuery

from bot.utils.database import users_collection
from bot.utils.language import get_response


class CallbackHandler:
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def handle_callback(self, callback: CallbackQuery):
        """Main method to handle callbacks from the user."""
        if callback.data.startswith('reply'):
            self._process_reply_callback(callback)

        self.bot.answer_callback_query(callback.id)

    def _process_reply_callback(self, callback: CallbackQuery):
        """Process the reply callback and set the replying state."""
        action, sender_id, message_id = callback.data.split('-')

        # Update the user's chat state to indicate they are replying
        self._set_replying_state(callback.from_user.id, message_id, sender_id)

        # Prompt the user to send their reply text
        self.bot.send_message(
            callback.from_user.id,
            get_response('texting.replying.send'),
            parse_mode='Markdown'
        )

    @staticmethod
    def _set_replying_state(user_id: int, message_id: str, sender_id: str):
        """Set the replying state in the database."""
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "replying": True,
                    "reply_target_message_id": message_id,
                    "reply_target_user_id": int(sender_id),
                }
            }
        )
