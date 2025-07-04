"""SupportManager handles support-related commands and interactions in the bot."""
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from telegram import CallbackQuery
from bot.languages.response import get_response
# from bot.common.database_utils import get_support_group
from bot.managers.start import StartBot
from bot.common.keyboard import KeyboardMarkupGenerator
class SupportManager:
    """Manager for handling support-related commands and interactions."""
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        # self.suppurt_group = get_support_group()
        self.keyboard = KeyboardMarkupGenerator()

    async def guide(self, msg: Message):
        """Handle the guide command to provide support instructions."""
        await self.bot.send_message(msg.chat.id, get_response('support.guide'), parse_mode='HTML',
                                    reply_markup=self.keyboard.guide_buttons())

    async def support(self, msg: Message):
        "Handle the support command to start a support session."
        await StartBot(self.bot).start(msg, 'support')

    async def faq_quiestions(self, callback: CallbackQuery):
        """Handle the FAQ command to provide frequently asked questions."""
        if callback.data == 'what_is_invischat':
            await self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=get_response('support.faq.what_is_invischat'),
                parse_mode='HTML',
                reply_markup=self.keyboard.return_to_faq_buttons()
            )
        elif callback.data == 'how_to_use':
            await self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=get_response('support.faq.how_to_use'),
                parse_mode='HTML',
                reply_markup=self.keyboard.return_to_faq_buttons()
            )
        elif callback.data == 'how_to_report_user':
            await self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=get_response('support.faq.how_to_report_user'),
                parse_mode='HTML',
                reply_markup=self.keyboard.return_to_faq_buttons()
            )
        elif callback.data == 'how_to_connect_to_speceific_user':
            await self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=get_response('support.faq.how_to_connect_to_speceific_user'),
                parse_mode='HTML',
                reply_markup=self.keyboard.return_to_faq_buttons()
            )
        else:
            await self.bot.answer_callback_query(callback.id,
                                                get_response('errors.unknown_action'),
                                                show_alert=True)
            return
