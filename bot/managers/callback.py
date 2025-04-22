from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InputTextMessageContent, \
    InlineQueryResultArticle, InlineQuery, ForceReply

from bot.common.chat_utils import close_chats, add_seen_message, get_seen_status
from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager
from bot.managers.nickname import NicknameManager
from bot.managers.settings import SettingsManager
from bot.managers.start import StartBot
from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.database_utils import fetch_user_data_by_id, update_user_fields, get_user_id, get_user_anon_id
from bot.common.user import is_subscribed_to_channel, is_bot_status_off
from bot.common.utils import generate_anon_link
from bot.admin.callback import AdminCallbackHandler
from bot.common.database_utils import is_user_banned

class CallbackHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def handle_callback(self, callback: CallbackQuery):
        """Main method to handle callbacks from the user."""
        callback_data = callback.data
        if is_user_banned(callback.from_user.id):
            await self.bot.send_message(callback.message.chat.id, get_response('account.ban.banned'),
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())
            return
        if callback_data.startswith('reply'):
            await self._process_reply_callback(callback)
        # elif callback_data.startswith('edit_message'):
        #     await self._process_edit_message_callback(callback)
        elif callback_data.startswith('joined'):
            await self._process_joined_channel(callback)
        elif callback_data.startswith('delete_message'):
            callback.data = callback_data.split('-')[1:]
            await self._process_delete_message_callback(callback)
        elif callback_data.startswith('seen'):
            callback.data = callback_data.split('-')[1:]
            await self._process_seen_callback(callback)
        elif callback_data.startswith('block'):
            await self._process_block_callback(callback)
        elif callback_data.startswith('report'):
            await self._process_report_callback(callback)
        elif callback_data.startswith('mark'):
            callback.data = callback_data.split('-')[1:]
            await self._process_mark_message(callback)
        elif callback_data.startswith('unblock'):
            await self._process_unblock_callback(callback)
        elif callback_data.startswith('change-nickname'):
            await self._process_change_nickname(callback)
        elif callback_data.startswith('change-bot_status'):
            await self._process_change_bot_status(callback)
        elif callback_data.startswith('cancel'):
            await self._process_cancel(callback)
        elif callback_data.startswith('admin'):
            await AdminCallbackHandler(bot=self.bot).handle_callback(callback)
        await self.bot.answer_callback_query(callback.id)


    async def handle_inline_query(self, inline: InlineQuery):
        """Handle inline queries for 'Text Me'."""
        user_id = inline.from_user.id
        text = inline.query.strip() or "حرفتو ناشناس بهم بزن 😉"  # Default text if empty

        # Generate the unique link for the user (user's ID or custom data)
        link = generate_anon_link(get_user_anon_id(user_id))

        # Create the inline message content with the text and button
        content = InputTextMessageContent(f"{text}")
        result = InlineQueryResultArticle(
            id=inline.id,
            title="متن خودت رو بنویس",
            description=text,
            input_message_content=content,
            thumbnail_url='https://s8.uupload.ir/files/photo_2024-10-20_02-07-59_h3tq.jpg',
            reply_markup=KeyboardMarkupGenerator().inline_text_me_button(link)  # Add the button below the message
        )

        # Send the inline query result back
        await self.bot.answer_inline_query(inline.id, results=[result])

        # Respond to the query
        await self.bot.answer_inline_query(inline.id, [result])

    async def _process_reply_callback(self, callback: CallbackQuery):
        """Process the reply callback and set the replying state."""
        action, sender_id, message_id = callback.data.split('-')
        # check if the user or the target user, bot status is off
        if is_bot_status_off(callback.from_user.id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.self.off'),
                show_alert=True
            )
            return
        elif is_bot_status_off(get_user_id(sender_id)):
            await self.bot.answer_callback_query(callback.id, get_response('account.bot_status.recipient.off'),
                                                 show_alert=True
                                                 )
            return
        # Update the user's chat state to indicate they are replying
        close_chats(callback.from_user.id)
        self._set_replying_state(callback.from_user.id, message_id, sender_id)

        # Prompt the user to send their reply text
        await self.bot.send_message(
            callback.from_user.id,
            get_response('texting.replying.send'),
            reply_to_message_id=callback.message.id,
            parse_mode='Markdown',
            reply_markup=KeyboardMarkupGenerator().cancel_buttons()
        )

    async def _process_seen_callback(self, callback: CallbackQuery):
        """Process the seen callback"""
        sender_anon_id, message_id = callback.data
        sender_id = get_user_id(sender_anon_id)
        # check if the user or the target user, bot status is off
        if is_bot_status_off(callback.from_user.id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.self.off'),
                show_alert=True
            )
            return
        elif is_bot_status_off(sender_id):
            await self.bot.answer_callback_query(callback.id, get_response('account.bot_status.recipient.off'),
                                                 show_alert=True
                                                 )
            return
        add_seen_message(callback.from_user.id, int(message_id)
                         )
        await self.bot.send_message(chat_id=sender_id, reply_to_message_id=message_id,
                                    text=get_response('texting.seen.recipient'))
        await self.bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.id,
                                                 reply_markup=KeyboardMarkupGenerator().recipient_buttons(
                                                     sender_anon_id, message_id, True))
        await self.bot.answer_callback_query(callback.id, get_response('texting.seen.sent'))

    async def _process_block_callback(self, callback: CallbackQuery):
        keyboard = KeyboardMarkupGenerator()
        if 'block' in callback.data.split('-'):
            action, sender_id, message_id = callback.data.split('-')
            if sender_id == fetch_user_data_by_id(callback.message.chat.id).get('id'):
                await self.bot.answer_callback_query(callback.id, get_response('blocking.self'))
                return
            if sender_id == 'support':
                await self.bot.answer_callback_query(callback.id, get_response('blocking.support'))
                return
            await self.bot.edit_message_reply_markup(callback.message.chat.id, callback.message.id,
                                                     callback.inline_message_id,
                                                     reply_markup=keyboard.block_confirmation_buttons(sender_id,
                                                                                                      message_id))
        elif 'block_confirm' in callback.data.split('-'):
            action, sender_id, message_id = callback.data.split('-')
            await BlockUserManager(self.bot).block_user(callback.message.chat.id, str(sender_id),
                                                        callback)
        elif 'block_cancel' in callback.data.split('-'):
            action, sender_id, message_id = callback.data.split('-')
            await BlockUserManager(self.bot).cancel_block(callback, message_id,
                                                          sender_id)

    async def _process_report_callback(self, callback: CallbackQuery):
        """Process the report callback"""
        await self.bot.answer_callback_query(callback.id, get_response('reporting.send'), show_alert=True)

    async def _process_edit_message_callback(self, callback: CallbackQuery):
        """Process the edit message callback"""
        action, recipient_message_id, recipient_anon_id = callback.data.split('-')
        prompt_message = await self.bot.send_message(callback.message.chat.id,
                                                     get_response('texting.tools.editing.send'),
                                                     reply_to_message_id=callback.message.id, reply_markup=ForceReply(
                input_field_placeholder='پیام جدید خود را بنویسید'))
        update_user_fields(callback.message.chat.id, {
            "editing_target_message_id": int(recipient_message_id),
            "editing_target_anon_id": str(recipient_anon_id),
            "editing_prompt_message_id": int(prompt_message.message_id)
        })

    async def _process_delete_message_callback(self, callback: CallbackQuery):
        """Process the delete message callback"""
        recipient_message_id, recipient_anon_id = callback.data
        await self.bot.delete_message(get_user_id(recipient_anon_id), int(recipient_message_id))
        await self.bot.edit_message_text(get_response('texting.tools.delete.deleted'), callback.message.chat.id,
                                         callback.message.id, parse_mode='Markdown')

    async def _process_unblock_callback(self, callback: CallbackQuery):
        keyboard = KeyboardMarkupGenerator()
        if 'unblock' in callback.data.split('-'):
            action, blocker_id, blocked_id, message_id = callback.data.split('-')
            await self.bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.id,
                                                     reply_markup=keyboard.unblock_confirmation_buttons(str(blocker_id),
                                                                                                        str(blocked_id),
                                                                                                        ))
        elif 'unblock_confirm' in callback.data.split('-'):
            action, blocker_id, blocked_id = callback.data.split('-')
            blocker_anon_id = users_collection.find_one({"user_id": callback.message.chat.id})['id']
            await BlockUserManager(self.bot).unblock_user(blocker_anon_id, str(blocked_id), callback)
        elif 'unblock_cancel' in callback.data.split('-'):
            action, blocker_id = callback.data.split('-')
            blocker_anon_id = users_collection.find_one({"user_id": callback.message.chat.id})['id']
            await BlockUserManager(self.bot).cancel_unblock_user(blocker_anon_id, str(blocker_id), callback.message.id)

    async def _process_change_nickname(self, callback: CallbackQuery):
        response = NicknameManager(self.bot).get_set_nickname_response(callback.message)
        await self.bot.edit_message_text(response, callback.message.chat.id, callback.message.id, parse_mode='Markdown',
                                         reply_markup=KeyboardMarkupGenerator().cancel_changing_nickname())

    async def _process_cancel(self, callback: CallbackQuery):
        action, task = callback.data.split('-')
        if task == "changing_nickname":
            update_user_fields(callback.from_user.id, 'awaiting_nickname', False)
            await self.bot.edit_message_text(AccountManager(self.bot).get_account_response(callback.message),
                                             callback.from_user.id, callback.message.id, parse_mode='Markdown',
                                             reply_markup=KeyboardMarkupGenerator().account_buttons())

    async def _process_change_bot_status(self, callback: CallbackQuery):
        await SettingsManager(self.bot).change_bot_status(callback)

    async def _process_mark_message(self, callback):
        sender_anon_id, message_id = callback.data
        seen = get_seen_status(user_id=callback.message.chat.id, message_id=callback.message.id)

        # Get the original text or caption
        if callback.message.text:
            original_text = callback.message.text
            is_caption = False
        elif callback.message.caption:
            original_text = callback.message.caption
            is_caption = True
        else:
            # No text or caption, send a response to the user and exit
            await self.bot.answer_callback_query(callback.id, "Cannot mark this message.")
            return

            # Check if the message is already marked
        if "#️⃣ #mark" in original_text:
            new_text = original_text.replace("\n #️⃣ #mark", "").strip()
            marked = False
        else:
            new_text = f"{original_text}\n #️⃣ #mark"
            marked = True

        # Edit the message appropriately (text or caption)
        if is_caption:
            await self.bot.edit_message_caption(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                caption=new_text,
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_anon_id, message_id, seen, marked)
            )
        else:
            await self.bot.edit_message_text(
                new_text,
                callback.message.chat.id,
                callback.message.id,
                reply_markup=KeyboardMarkupGenerator().recipient_buttons(sender_anon_id, message_id, seen, marked)
            )

    async def _process_joined_channel(self, callback):
        if not await is_subscribed_to_channel(self.bot, callback.message.chat.id):
            await self.bot.answer_callback_query(callback.id, get_response('ad.not_joined'), show_alert=True)
            return
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)
        await StartBot(self.bot).start(callback.message)

    @staticmethod
    def _set_replying_state(user_id: int, message_id: str, sender_id: str):
        """Set the replying state in the database."""
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "replying": True,
                    "reply_target_message_id": message_id,
                    "reply_target_user_id": str(sender_id),
                },
            }
        )
