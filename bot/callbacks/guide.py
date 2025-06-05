"""Handles guide-related callbacks for the bot."""
from telebot.types import CallbackQuery

from bot.languages.response import get_response
from bot.managers.support import SupportManager
from bot.common.keyboard import KeyboardMarkupGenerator
class GuideCallbackHandler:
    """Handles guide-related callbacks for the bot."""
    def __init__(self, bot):
        self.bot = bot
        self.support_manager = SupportManager(bot)
        self.keyboard = KeyboardMarkupGenerator()
        self.callback_handlers = {
            'faq': self._process_faq_callback,
            'support': self._process_support_callback,
            'return_to_guide': self._process_return_to_guide_callback,
        }

    async def handle_callbacks(self, callback: CallbackQuery):
        """Handle the guide callbacks to provide right processor."""
        action = callback.data.split('-')[0]
        handler = self.callback_handlers.get(action)
        if handler:
            await handler(callback)
        else:
            await self.bot.answer_callback_query(callback.id,
                                                get_response('errors.unknown_action'),
                                                show_alert=True)

    async def _process_faq_callback(self, callback: CallbackQuery):
        """Process the FAQ callback."""
        if len(callback.data.split('-')) > 1:
            callback.data = callback.data.split('-')[1]
            await self.support_manager.faq_quiestions(callback)
            return
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=get_response('support.faq.explanation'),
            parse_mode='HTML',
            reply_markup=self.keyboard.faq_buttons()
        )

    async def _process_support_callback(self, callback: CallbackQuery):
        """Process the support callback."""
        await self.support_manager.support(callback.message)

    async def _process_return_to_guide_callback(self, callback: CallbackQuery):
        """Process the return to guide callback."""
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=get_response('support.guide'),
            parse_mode='HTML',
            reply_markup=self.keyboard.guide_buttons()
        )
