"""Callback handler for processing user interactions with the bot."""
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InputTextMessageContent,\
      InlineQueryResultArticle, InlineQuery
from telegram import ReactionTypeEmoji
from bot.callbacks.guide import GuideCallbackHandler
from bot.common.chat_utils import close_chats, add_seen_message, get_seen_status
from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager
from bot.managers.link import LinkManager
from bot.managers.nickname import NicknameManager
from bot.managers.settings import SettingsManager
from bot.managers.start import StartBot
from bot.database.database import users_collection
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.database_utils import add_reaction, close_metadata, fetch_user_data_by_id, get_reactions,\
        update_last_interaction_time, update_user_fields,\
        get_user_id, get_user_anon_id
from bot.common.user import is_subscribed_to_channel, is_bot_status_off
from bot.common.utils import generate_anon_link
from bot.admin.callback import AdminCallbackHandler
from bot.common.database_utils import is_user_banned


class CallbackManager:
    """CallbackHandler is a class responsible for handling various callback queries &
    inline queries received by the bot.
    It processes user interactions and executes the appropriate actions based 
    on the callback data."""

    def __init__(self, bot: AsyncTeleBot):
        """Initialize the CallbackHandler with the bot instance."""
        self.bot = bot
        self.callback_handlers = {
            'joined': self._process_joined_channel,
            'reply': self._process_reply_callback,
            'delete_message': self._process_delete_message_callback,
            'recipient_option': self._process_recipient_option_callback,
            'reactions': self._process_reactions_callback,
            'reaction': self._process_reaction_action_callback,
            'seen': self._process_seen_callback,
            'block': self._process_block_action,
            'block_cancel': self._process_block_action_cancel,
            'block_confirm': self._process_block_action_confirm,
            'report': self._process_report_callback,
            'mark': self._process_mark_message,
            'unblock': self._process_unblock_action,
            'unblock_cancel': self._process_unblock_action_cancel,
            'unblock_confirm': self._process_unblock_action_confirm,
            'return_to_recipient_buttons': self._process_return_to_recipient_buttons,
            'return_to_recipient_option_buttons': self._process_return_to_recipient_option_buttons,
            'change_nickname': self._process_change_nickname,
            'change_bot_status': self._process_change_bot_status,
            'cancel': self._process_cancel,
            'admin': self._process_admin_callback,
            'regenerate_link': self._process_regenarate_link,
            'cancel_regenerate_link': self._process_cancel_regenerate_link,
            'confirm_regenerate_link': self._process_confirm_regenerate_link,
            'placeholder': self._process_placeholder,
            'guide': self._process_guide_callback,  # Placeholder for unknown actions
        }
        self.keyboard = KeyboardMarkupGenerator()
        self.blocker = BlockUserManager(self.bot)

    async def handle_callback(self, callback: CallbackQuery):
        """Main method to handle callbacks from the user."""
        callback_data = callback.data

        if is_user_banned(callback.from_user.id):
            await self._send_ban_message(callback)
            return
        # store the last interaction time
        await update_last_interaction_time(callback.from_user.id)
        # Extract the action type from the callback data
        action = callback_data.split('-')[0]
        # Find and execute the corresponding handler
        handler = self.callback_handlers.get(action)
        if handler:
            callback.data = callback_data.split('-', 1)[-1]  # Remove action from data
            await handler(callback)
        else:
            await self.bot.answer_callback_query(callback.id,
                                                get_response('errors.unknown_action'),
                                                show_alert=True)

        await self.bot.answer_callback_query(callback.id)

    async def handle_inline_query(self, inline: InlineQuery):
        """Handle inline queries."""
        user_id = inline.from_user.id
        anon_id = get_user_anon_id(user_id)
        text = inline.query.strip() or "حرفتو ناشناس بهم بزن 😉"  # Default text if empty
        link = generate_anon_link(anon_id)

        content = InputTextMessageContent(f"{text}")
        result = InlineQueryResultArticle(
            id=inline.id,
            title="بزن اینجا تا پیامت فرستاده بشه.",
            description=text,
            input_message_content=content,
            thumbnail_url='https://s8.uupload.ir/files/photo_2024-10-20_02-07-59_h3tq.jpg',
            reply_markup=self.keyboard.inline_text_me_button(link)
        )

        await self.bot.answer_inline_query(inline.id, results=[result], cache_time=0)

    async def _send_ban_message(self, callback: CallbackQuery):
        """Send a message to banned users."""
        await self.bot.send_message(
            callback.message.chat.id,
            get_response('account.ban.banned'),
            reply_markup=self.keyboard.main_buttons()
        )

    async def _process_reply_callback(self, callback: CallbackQuery):
        """Process the reply callback and set the replying state."""
        sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_user_id = get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return
        if await self._check_bot_status(callback, sender_user_id):
            return

        await close_chats(callback.from_user.id)
        await close_metadata(callback.from_user.id)
        self._set_replying_state(callback.from_user.id, message_id, sender_anon_id)

        await self.bot.send_message(
            callback.from_user.id,
            get_response('texting.replying.send'),
            reply_to_message_id=callback.message.id,
            parse_mode='Markdown',
            reply_markup=self.keyboard.cancel_buttons()
        )

    async def _process_recipient_option_callback(self, callback: CallbackQuery):
        """Process the recipient option callback."""
        sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_user_id = get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return

        if await self._check_bot_status(callback, sender_user_id):
            return

        seen = get_seen_status(user_id=callback.message.chat.id, message_id=message_id)
        marked = '📍 #نشان' in (callback.message.text or callback.message.caption or '')
        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.recipient_option_buttons(sender_anon_id, message_id,
                                                                 is_seen=seen, is_marked=marked)
        )

    async def _process_reactions_callback(self, callback: CallbackQuery):
        """Process the reaction callback."""
        sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_user_id = get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return

        if await self._check_bot_status(callback, sender_user_id):
            return
        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.reaction_buttons(sender_anon_id,
                                                message_id,
                                                toggled_emoji=await get_reactions(sender_user_id,
                                                                                    message_id))
        )

    async def _process_reaction_action_callback(self, callback: CallbackQuery):
        """Process the reaction action callback."""
        reaction, sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_user_id = get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return

        if await self._check_bot_status(callback, sender_user_id):
            return

        emojies = {
            'like': '👍',
            'dislike': '👎',
            'heart': '❤️',
            'fire': '🔥',
            'smile': '😁',
            'laugh': '🤣',
            'thanks': '🙏',
            'clap': '👏',
            'sad':'😢',
            'cry':'😭',
            'angry':'😡',
            'thinking':'🤔',
            'chad': '🗿',
            'moon':'🌚',
        }
        reaction = emojies.get(reaction, reaction)
        # Check if the user has already reacted to the message
        existing_reaction = await get_reactions(sender_user_id, message_id)
        if existing_reaction and existing_reaction != 'هیج ریاکشنی ندادی':
            # If the reaction is the same as the existing one, dont do anything
            try:
                # Update the reaction but do not send a notification
                await self.bot.edit_message_reply_markup(
                    callback.message.chat.id,
                    message_id=callback.message.id,
                    reply_markup=self.keyboard.reaction_buttons(sender_anon_id,
                                                                message_id,
                                                                toggled_emoji=reaction)
                )
                await self.bot.set_message_reaction(
                chat_id=int(sender_user_id),
                message_id=int(message_id),
                reaction=[ReactionTypeEmoji(emoji=reaction)],
                is_big=False
            )
                await add_reaction(sender_user_id, message_id, emoji=reaction)
            except Exception:
                await self.bot.answer_callback_query(callback.id,
                                                    get_response('errors.same_reaction'))                             
            return

        # Update the reaction and send a notification
        await add_reaction(sender_user_id, message_id, emoji=reaction)
        await self.bot.set_message_reaction(
            chat_id=int(sender_user_id),
            message_id=int(message_id),
            reaction=[ReactionTypeEmoji(emoji=reaction)],
            is_big=False
        )
        await self.bot.send_message(
            chat_id=sender_user_id,
            reply_to_message_id=int(message_id),
            text=get_response('texting.reaction.recipient'),
            parse_mode='Markdown'
        )

        await self.bot.edit_message_reply_markup(
            callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.reaction_buttons(sender_anon_id, message_id,
                                                        toggled_emoji=reaction)
        )

    async def _process_seen_callback(self, callback: CallbackQuery):
        """Process the seen callback."""
        sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_id = get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return

        if await self._check_bot_status(callback, sender_id):
            return

        add_seen_message(callback.from_user.id, int(message_id))
        await self.bot.send_message(
            chat_id=sender_id,
            reply_to_message_id=message_id,
            text=get_response('texting.seen.recipient')
        )
        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.recipient_option_buttons(sender_anon_id, message_id,True)
        )
        await self.bot.answer_callback_query(callback.id, get_response('texting.seen.sent'))


    async def _process_block_action(self, callback: CallbackQuery):
        """Process the block action callback."""
        sender_id, message_id = callback.data.split('-')

        if not await self._validate_block_action(callback, sender_id):
            return
        await self.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                reply_markup=self.keyboard.block_confirmation_buttons(sender_id, message_id)
            )

    async def _process_block_action_confirm(self, callback: CallbackQuery):
        """Process the block confirmation callback."""
        sender_id, _ = callback.data.split('-')
        if not await self._validate_block_action(callback, sender_id):
            return
        await self.blocker.block_user(callback.message.chat.id, sender_id, callback)
    async def _process_block_action_cancel(self, callback: CallbackQuery):
        """Process the block cancellation callback."""
        sender_id, message_id = callback.data.split('-')
        if not await self._validate_block_action(callback, sender_id):
            return
        await self.blocker.cancel_block(callback, message_id, sender_id)


    async def _process_unblock_action(self, callback: CallbackQuery):
        """Process the unblock callback."""
        blocker_id, blocked_id = callback.data.split('-')
        if await self._check_bot_status(callback, callback.from_user.id):
            return

        await self.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                reply_markup=self.keyboard.unblock_confirmation_buttons(blocker_id, blocked_id)
            )
    async def _process_unblock_action_cancel(self, callback: CallbackQuery):
        """Process the unblock cancel callback."""
        blocker_id, _ = callback.data.split('-')

        if await self._check_bot_status(callback, callback.from_user.id):
            return

        await self.blocker.cancel_unblock_user(blocker_id, callback.message.id)
    async def _process_unblock_action_confirm(self, callback: CallbackQuery):
        """Process the unblock confirmation callback."""
        _, blocked_id = callback.data.split('-')

        if await self._check_bot_status(callback, callback.from_user.id):
            return

        blocker_anon_id = users_collection.find_one({"user_id": callback.message.chat.id})['id']
        await self.blocker.unblock_user(blocker_anon_id, blocked_id, callback)

    async def _process_delete_message_callback(self, callback: CallbackQuery):
        """Process the delete message callback"""
        recipient_message_id, recipient_anon_id = callback.data.split('-')
        await self.bot.delete_message(get_user_id(recipient_anon_id), int(recipient_message_id))
        await self.bot.edit_message_text(get_response('texting.tools.delete.deleted'),
                                         callback.message.chat.id,
                                         callback.message.id, parse_mode='Markdown')
    async def _process_report_callback(self, callback: CallbackQuery):
        """Process the report callback"""
        await self.bot.answer_callback_query(callback.id,
                                            get_response('reporting.send'), show_alert=True)

    async def _process_change_nickname(self, callback: CallbackQuery):
        """Process the change nickname callback."""
        await close_chats(callback.message.chat.id, True)
        response = NicknameManager(self.bot).get_set_nickname_response(callback.message)
        await self.bot.edit_message_text(
            response,
            callback.message.chat.id,
            callback.message.id,
            parse_mode='Markdown',
            reply_markup=self.keyboard.cancel_changing_nickname()
        )

    async def _process_cancel(self, callback: CallbackQuery):
        """Process the cancel callback."""
        task = callback.data
        if task == "changing_nickname":
            await update_user_fields(callback.from_user.id, 'awaiting_nickname', False)
            await self.bot.edit_message_text(
                AccountManager(self.bot).get_account_response(callback.message),
                callback.from_user.id,
                callback.message.id,
                parse_mode='Markdown',
                reply_markup=self.keyboard.account_buttons()
            )

    async def _process_change_bot_status(self, callback: CallbackQuery):
        """Process the change bot status callback."""
        await SettingsManager(self.bot).change_bot_status(callback)

    async def _process_mark_message(self, callback: CallbackQuery):
        """Process the mark message callback."""
        sender_anon_id, message_id = callback.data.split('-')
        seen = get_seen_status(user_id=callback.message.chat.id, message_id=callback.message.id)

        original_text, is_caption = self._get_message_text_or_caption(callback)
        if not original_text:
            await self.bot.answer_callback_query(callback.id, "Cannot mark this message.")
            return

        new_text, marked = self._toggle_mark(original_text)

        await self._edit_message(callback, new_text, sender_anon_id,
                                  message_id, seen, marked, is_caption)

    async def _process_return_to_recipient_buttons(self, callback: CallbackQuery):
        """Process the return to recipient buttons callback."""
        sender_anon_id, message_id = callback.data.split('-')

        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.recipient_buttons(sender_anon_id, message_id)
        )

    async def _process_return_to_recipient_option_buttons(self, callback: CallbackQuery):
        """Process the return to recipient option buttons callback."""
        sender_anon_id, message_id = callback.data.split('-')
        seen = get_seen_status(user_id=callback.message.chat.id, message_id=message_id)
        marked = '📍 #نشان' in (callback.message.text or callback.message.caption or '')

        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.recipient_option_buttons(sender_anon_id, message_id,
                                                                 is_seen=seen, is_marked=marked)
        )

    async def _process_regenarate_link(self, callback: CallbackQuery):
        """Process the change link callback."""
        await self.bot.send_message(callback.message.chat.id,
                                   get_response('link.regenerate_link.confirm'),
                                   reply_markup=self.keyboard.regenarate_link_buttons(),
                                   parse_mode='Markdown')

    async def _process_cancel_regenerate_link(self, callback: CallbackQuery):
        """Process the cancel regenerate link callback."""
        await self.bot.answer_callback_query(callback.id,
                                             get_response('link.regenerate_link.cancel'),
                                             show_alert=True)
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)

    async def _process_confirm_regenerate_link(self, callback: CallbackQuery):
        """Process the confirm regenerate link callback."""
        user_id = callback.message.chat.id
        link_manager = LinkManager(self.bot)
        await link_manager.regenerate_link(callback.message)
        await self.bot.delete_message(user_id, callback.message.id)

    async def _process_joined_channel(self, callback: CallbackQuery):
        """Process the joined channel callback."""
        if not await is_subscribed_to_channel(self.bot, callback.message.chat.id):
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('ad.not_joined'), show_alert=True)
            return
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)
        await StartBot(self.bot).start(callback.message)

    async def _process_admin_callback(self, callback: CallbackQuery):
        """Delegate admin-related callbacks to the AdminCallbackHandler."""
        await AdminCallbackHandler(self.bot).handle_callback(callback)

    async def _process_placeholder(self, callback: CallbackQuery):
        """Handle unknown or placeholder actions."""
        await self.bot.answer_callback_query(callback.id,
                                             get_response('errors.placeholder'))
        
    async def _process_guide_callback(self, callback: CallbackQuery):
        """Handle guide-related callbacks."""
        await GuideCallbackHandler(self.bot).handle_callbacks(callback)

    @staticmethod
    def _set_replying_state(user_id: int, message_id: str, sender_anon_id: str):
        """Set the replying state in the database."""
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "replying": True,
                    "reply_target_message_id": message_id,
                    "reply_target_user_id": str(sender_anon_id),
                },
            }
        )

    @staticmethod
    def _get_message_text_or_caption(callback: CallbackQuery):
        """Get the text or caption of a message."""
        if callback.message.text:
            return callback.message.text, False
        elif callback.message.caption:
            return callback.message.caption, True
        return None, False

    @staticmethod
    def _toggle_mark(original_text: str):
        """Toggle the mark status of a message."""
        if "📍 #نشان" in original_text.strip():
            return original_text.replace("\n📍 #نشان", "").strip(), False

        # Split the text into lines
        lines = original_text.strip().split("\n")
        if len(lines) > 1:
            # Insert the mark before the last line
            lines.insert(-1, "📍 #نشان")
        else:
            # If there's only one line, append the mark
            lines.append("📍 #نشان")

        return "\n".join(lines), True

    async def _edit_message(self, callback, new_text, sender_anon_id,
                            message_id, seen, marked, is_caption):
        """Edit the message text or caption."""
        if is_caption:
            await self.bot.edit_message_caption(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                caption=new_text,
                reply_markup=self.keyboard.recipient_option_buttons(sender_anon_id, message_id,
                                                             is_seen=seen, is_marked=marked),
            )
        else:
            await self.bot.edit_message_text(
                new_text,
                callback.message.chat.id,
                callback.message.id,
                reply_markup=self.keyboard.recipient_option_buttons(sender_anon_id, message_id,
                                                             is_seen=seen, is_marked=marked),
            )

    async def _check_bot_status(self, callback: CallbackQuery, user_id: str):
        """Verify if the bot status is disabled for the current user or the recipient."""
        if is_bot_status_off(callback.from_user.id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.self.disabled'),
                show_alert=True
            )
            return True
        if is_bot_status_off(user_id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.recipient.disabled'),
                show_alert=True
            )
            return True
        return False

    async def _validate_block_action(self, callback: CallbackQuery, sender_id: str):
        """Validate block action to prevent blocking self or support."""
        if sender_id == fetch_user_data_by_id(callback.message.chat.id).get('id'):
            await self.bot.answer_callback_query(callback.id, get_response('blocking.self'))
            return False
        if sender_id == 'support':
            await self.bot.answer_callback_query(callback.id, get_response('blocking.support'))
            return False
        return True
