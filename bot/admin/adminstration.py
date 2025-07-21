"""
This file contains the main adminstration class and its methods.
from telebot.async_telebot import AsyncTeleBot
"""

from telebot.types import Message
from telebot.asyncio_helper import ApiTelegramException
from bot.admin.keyboard import Keyboard
from bot.common.data import BotDataManager, UserDataManager
from bot.common.utils import convert_timestamp_to_date
from bot.languages.response import get_response
from telebot.async_telebot import AsyncTeleBot

class Admin:
    """
    Admin class to handle admin operations.
    """
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.bot_manager = BotDataManager()
        self.user_manager = UserDataManager()
        self.keyboard = Keyboard()

    async def main(self, msg: Message):
        """
        Main admin panel
        :param msg: Message object
        """
        if not await self.bot_manager.is_admin(msg.from_user.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.panel',
                                                              name=msg.from_user.first_name),
                                        reply_markup=self.keyboard.main_panel(), parse_mode='Markdown')

    async def announce_new_user(self, user_id: int):
        """
        Announce new user to all admins
        :param user_id: ID of the new user
        """
        await self.user_manager.bind_user(user_id)
        user_data = await self.user_manager.fetch_user()
        stats_data = {
            "first_name": user_data.get('profile', 'N/A').get('first_name', 'N/A'),
            "last_name": user_data.get('profile', 'N/A').get('last_name', 'N/A'),
            "anon_id": str(user_data.get('anon_id', 'N/A')),
            "username": user_data.get('profile', 'N/A').get('username', 'N/A'),
            "user_id": int(user_data.get('user_id', 0)),
            "nickname": user_data.get('profile', 'N/A').get('nickname', 'N/A'),
            "joined_at": convert_timestamp_to_date(user_data.get('metadata',
                                                                []).get('joined_at', None),
                                                                "datetime"),

        }
        for admin in await self.bot_manager.get_admins():
            await self.bot.send_message(
                admin,
                get_response('admin.stats.new_user',
                             **stats_data),
                parse_mode='Markdown'
            )

    async def ahelp(self, msg: Message):
        """
        Help command for admin
        :param msg: Message object
        """
        if not await self.bot_manager.is_admin(msg.from_user.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.help'), parse_mode='Markdown')

    async def activate_broadcast(self, msg: Message):
        """
        Broadcast message to all users
        :param msg: Message object
        """
        await self.user_manager.bind_user(msg.chat.id)
        if not await self.bot_manager.is_admin(msg.chat.id):
            await self.bot.send_message(msg.chat.id, get_response('errors.no_active_chat'))
            return
        await self.bot.send_message(msg.chat.id, get_response('admin.broadcast.send'), reply_markup= self.keyboard.broadcast_buttons())
        # Here you would implement the logic to send a broadcast message to all users.
        await self.user_manager.update_fields({'admin.broadcast': True})

    async def broadcast(self, msg: Message):
        users_ids = await self.bot_manager.get_all_user_ids()
        users_count = len(users_ids)
        caption = msg.caption or ''
        content = msg.content_type

        # Map content types to:
        # (send_method, attribute name, whether to include caption)
        content_map = {
            'text': (self.bot.send_message, None, False),
            'photo': (self.bot.send_photo, 'photo', True),
            'video': (self.bot.send_video, 'video', True),
            'audio': (self.bot.send_audio, 'audio', True),
            'voice': (self.bot.send_voice, 'voice', True),
            'document': (self.bot.send_document, 'document', True),
            'sticker': (self.bot.send_sticker, 'sticker', False),
            'animation': (self.bot.send_animation, 'animation', True),
        }

        if content not in content_map:
            # fallback for unknown types
            return

        send_method, file_attr, has_caption = content_map[content]
        for user_id in users_ids:
            try:
                if content == 'text':
                    print(msg.entities)
                    await send_method(user_id, msg.text, entities=msg.entities)


                elif file_attr:
                    # Get the file_id dynamically
                    if content == 'photo':
                        file_id = getattr(msg, file_attr)[-1].file_id
                    else:
                        file_id = getattr(msg, file_attr).file_id

                    if has_caption:
                        await send_method(user_id, file_id, caption=caption, caption_entities=msg.caption_entities)
                    else:
                        await send_method(user_id, file_id)

                else:
                    # Shouldn't reach here, but safe fallback
                    await send_method(msg.chat.id, "Unsupported content.")
            except ApiTelegramException:
                users_count -= 1
                continue
        await self.user_manager.bind_user(msg.chat.id)
        await self.user_manager.update_fields({'admin.broadcast': False})
        await self.bot.send_message(msg.chat.id, get_response('admin.broadcast.sent', users_count=users_count))

    async def cancel_broadcast(self, msg: Message):
        await self.user_manager.bind_user(msg.chat.id)
        await self.user_manager.update_fields({'admin.broadcast': False})
        await self.bot.delete_message(msg.chat.id, msg.message_id)
        await self.bot.send_message(msg.chat.id, get_response('admin.broadcast.cancel'))
