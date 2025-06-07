from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.common.chat_utils import close_chats
from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.utils import generate_anon_link
from decouple import config
from bot.common.database_utils import close_metadata, get_user_anon_id, get_user_anon_id_by_username, update_user_fields
from bot.common.utils import create_unique_id
from bot.managers.start import StartBot
class LinkManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.bot_username = config('BOT_USERNAME', default='')
        self.keyboard = KeyboardMarkupGenerator()

    async def link(self, msg: Message):
        user_bot_id = users_collection.find_one({"user_id": msg.from_user.id})['id']
        link: str = generate_anon_link(user_bot_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.link', link=link),
            parse_mode='HTML',
            reply_markup=self.keyboard.share_link_buttons(
                get_response('link.share_link'), link)
        )
    async def regenerate_link(self, msg: Message):
        """Regenerate the anonymous link for the user."""
        new_id = create_unique_id()
        await update_user_fields(
            msg.chat.id,
            'id',
            new_id
        )
        new_link: str = generate_anon_link(new_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.regenerate_link.regenerated', link=new_link),
            parse_mode='HTML',
            reply_markup=self.keyboard.share_link_buttons(
                get_response('link.share_link'), new_link)
        )
    async def send_without_link(self, msg: Message):
        """Send a message without the anonymous link."""
        await close_chats(msg.from_user.id, True)
        await update_user_fields(
            msg.chat.id,
            'send_without_link',
            True
        )
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.connect_without_link.send_without_link'),
            parse_mode='HTML',
            reply_markup=self.keyboard.cancel_buttons()
        )
    async def connect_without_link(self, msg: Message):
        """Connect with the user without using the anonymous link."""
        user_id = msg.from_user.id
        target_user_anon_id = ''
        if msg.forward_from:
            target_user_anon_id = get_user_anon_id(msg.forward_from.id)
        elif msg.text.strip().startswith('@'):
            target_user_anon_id = await get_user_anon_id_by_username(msg.text[1:].lower())
        elif msg.text.isdigit():
            target_user_anon_id = get_user_anon_id(int(msg.text))
        if not target_user_anon_id:
            await self.bot.send_message(
                msg.chat.id,
                get_response('link.connect_without_link.not_found'),
                parse_mode='HTML',
                reply_markup=self.keyboard.cancel_buttons()
            )
            return
        await close_metadata(user_id, 'send_without_link')
        await StartBot(self.bot).start(msg, target_user_anon_id)
