"""Manager for handling anonymous links and user connections."""
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from decouple import config
from bot.common.data import ChatDataManager, UserDataManager
from bot.common.data import get_user_anon_id, get_anon_id_by_username
from bot.common.threads import delete_message
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.utils import generate_anon_link, create_unique_id
from bot.managers.start import StartBot

class LinkManager:
    """Manager for handling anonymous links and user connections."""
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.bot_username = config('BOT_USERNAME', default='')
        self.keyboard = KeyboardMarkupGenerator()
        self.user_manager = UserDataManager()
        self.chat_manager = ChatDataManager()

    async def link(self, msg: Message):
        """Generate and send the anonymous link to the user."""
        await self.user_manager.bind_user(msg.from_user.id)
        user_anon_id = await self.user_manager.get_anon_id()
        link: str = generate_anon_link(user_anon_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.link', link=link),
            parse_mode='HTML',
            reply_markup=self.keyboard.share_link_buttons(
                get_response('link.share_link'), link)
        )

    async def revoke_link(self, msg: Message):
        """Regenerate the anonymous link for the user."""
        await self.user_manager.bind_user(msg.chat.id)
        new_anon_id = await create_unique_id()
        await self.user_manager.update_fields('anon_id', new_anon_id)
        new_link: str = generate_anon_link(new_anon_id)
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.revoke_link.revoked', link=new_link),
            parse_mode='HTML',
            reply_markup=self.keyboard.share_link_buttons(
                get_response('link.share_link'), new_link)
        )

    async def send_without_link(self, msg: Message):
        """Send a message without the anonymous link."""
        await self.user_manager.bind_user(msg.from_user.id)
        await self.chat_manager.close_chats(msg.from_user.id, True)
        await self.user_manager.toggle_flag("send_without_link", True)
        await self.bot.send_message(
            msg.chat.id,
            get_response('link.connect_without_link.send_without_link'),
            parse_mode='HTML',
            reply_markup=self.keyboard.cancel_buttons()
        )

    async def connect_without_link(self, msg: Message):
        """Connect with the user without using the anonymous link."""
        await self.user_manager.bind_user(msg.from_user.id)
        target_user_anon_id = None
        if msg.forward_from:
            target_user_anon_id = await get_user_anon_id(msg.forward_from.id)
        elif msg.text.strip().startswith('@'):
            target_user_anon_id = await get_anon_id_by_username(msg.text[1:].lower())
        elif msg.text.isdigit():
            target_user_anon_id = await get_user_anon_id(int(msg.text))
        if not target_user_anon_id:
            await self.bot.send_message(
                msg.chat.id,
                get_response('link.connect_without_link.not_found'),
                parse_mode='HTML',
                reply_markup=self.keyboard.cancel_buttons()
            )
            return
        await self.user_manager.toggle_flag("send_without_link", False)
        connecting = await self.bot.send_message(
            msg.from_user.id,
            get_response('link.connect_without_link.found'),
            parse_mode="HTML"
        )
        await delete_message(self.bot, msg.from_user.id, connecting.id, 1)
        await StartBot(self.bot).start(msg, target_user_anon_id)
