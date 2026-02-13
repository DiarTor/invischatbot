"""Callback handler for processing user interactions with the bot."""
from datetime import datetime
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InputTextMessageContent,\
      InlineQueryResultArticle, InlineQuery, ReactionTypeEmoji
from bot.callbacks.guide import GuideCallbackHandler
from bot.managers.account import AccountManager
from bot.managers.block import BlockUserManager
from bot.managers.link import LinkManager
from bot.managers.nickname import NicknameManager
from bot.managers.settings import SettingsManager
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.utils import generate_anon_link
from bot.admin.callback import AdminCallbackHandler
from bot.common.data import UserDataManager, ChatDataManager
from bot.common.data import get_user_id, get_user_anon_id, find_one, mongo

class CallbackManager:
    """CallbackHandler is a class responsible for handling various callback queries &
    inline queries received by the bot.
    It processes user interactions and executes the appropriate actions based 
    on the callback data."""

    def __init__(self, bot: AsyncTeleBot):
        """Initialize the CallbackHandler with the bot instance."""
        self.bot = bot
        self.callback_handlers = {
            'reply': self._process_reply_callback,
            'delete_message': self._process_delete_message_callback,
            'recipient_option': self._process_recipient_option_callback,
            'reactions': self._process_reactions_callback,
            'reaction': self._process_reaction_action_callback,
            'seen': self._process_seen_callback,
            'block': self._process_block_action,
            'block_cancel': self._process_block_action_cancel,
            'block_confirm': self._process_block_action_confirm,
            'unblock_shortcut': self._process_unblock_shortcut_action,
            'add_note': self._process_add_note_request,
            'read_note': self._process_read_note_request,
            'mark': self._process_mark_message,
            'blocklist_page': self._process_blocklist_page,
            'unblock': self._process_unblock_action,
            'unblock_cancel': self._process_unblock_action_cancel,
            'unblock_confirm': self._process_unblock_action_confirm,
            'unblock_all': self._process_unblock_all_request,
            'unblock_all_cancel': self._process_unblock_all_request_cancel,
            'unblock_all_confirm': self._process_unblock_all_request_confirm,
            'return_to_recipient_buttons': self._process_return_to_recipient_buttons,
            'return_to_recipient_option_buttons': self._process_return_to_recipient_option_buttons,
            'change_nickname': self._process_change_nickname,
            'change_bio': self._process_change_bio,
            'change_bot_status': self._process_change_bot_status,
            'cancel': self._process_cancel,
            'admin': self._process_admin_callback,
            'revoke_link': self._process_revoke_link,
            'cancel_revoke_link': self._process_cancel_revoke_link,
            'confirm_revoke_link': self._process_confirm_revoke_link,
            'placeholder': self._process_placeholder,
            'guide': self._process_guide_callback,  # Placeholder for unknown actions
        }
        self.keyboard = KeyboardMarkupGenerator()
        self.blocker = BlockUserManager(self.bot)
        self.user_manager = UserDataManager(self.bot)
        self.chat_manager = ChatDataManager()

    async def handle_callback(self, callback: CallbackQuery):
        """Main method to handle callbacks from the user."""
        callback_data = callback.data
        await self.user_manager.bind_user(callback.from_user.id)

        if await self.user_manager.is_banned():
            await self.bot.send_message(
            callback.message.chat.id,
            get_response('account.ban.banned'),
            reply_markup=self.keyboard.main_buttons()
        )
            return

        # store the last interaction time
        await self.user_manager.update_last_interaction()

        # Extract the action type from the callback data
        action = callback_data.split('-')[0]

        # Find and execute the corresponding handler
        handler = self.callback_handlers.get(action)
        if handler:
            if action in ['admin']:
                # For admin actions, we pass the callback directly to the handler
                await handler(callback)
            else:
                callback.data = callback_data.split('-', 1)[-1]  # Remove action from data
                await handler(callback)
        else:
            await self.bot.answer_callback_query(callback.id,
                                                get_response('errors.unknown_action'),
                                                show_alert=True)

    async def handle_inline_query(self, inline: InlineQuery):
        """Handle inline queries."""
        await self.user_manager.bind_user(inline.from_user.id)
        anon_id = await self.user_manager.get_anon_id()
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

    async def _process_reply_callback(self, callback: CallbackQuery):
        """Process the reply callback and set the replying state."""
        sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_user_id = await get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return
        if await self._check_bot_status(callback, sender_user_id):
            return

        if await self.blocker.is_user_blocked(sender_anon_id, callback.from_user.id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('blocking.blocked_by_user'),
                show_alert=True)
            return

        await self.chat_manager.close_chats(callback.from_user.id)
        await self.user_manager.close_metadata()
        await self.chat_manager.update_replying_state(callback.message.chat.id, message_id, sender_anon_id)

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
            sender_user_id = await get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return

        if await self._check_bot_status(callback, sender_user_id):
            return

        seen = await self.chat_manager.has_seen_message(callback.message.chat.id, callback.message.id)
        marked = self.chat_manager.is_text_marked(callback.message.text or callback.message.caption)
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
            sender_user_id = await get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return

        if await self._check_bot_status(callback, sender_user_id):
            return
        reactions = await self.chat_manager.get_reaction(sender_user_id, message_id)
        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.reaction_buttons(sender_anon_id,
                                                message_id,
                                                toggled_emoji=reactions))

    async def _process_reaction_action_callback(self, callback: CallbackQuery):
        """Process the reaction action callback."""
        reaction, sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_user_id = await get_user_id(sender_anon_id)
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
        existing_reaction = await self.chat_manager.get_reaction(sender_user_id, message_id)
        if existing_reaction and existing_reaction != 'هیچ ریاکشنی ندادی':
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
                await self.chat_manager.add_reaction(sender_user_id, message_id, emoji=reaction)
                await self.bot.answer_callback_query(callback.id,
                                                     get_response('texting.reaction.how_to_remove'))
            except Exception:
                #remove the reaction from the message if the reaction is the same as the existing one
                await self.bot.set_message_reaction(
                    chat_id=int(sender_user_id),
                    message_id=int(message_id),
                    reaction=[],
                    is_big=False
                )
                await self.chat_manager.remove_reaction(sender_user_id, message_id)
                await self.bot.edit_message_reply_markup(
                    callback.message.chat.id,
                    message_id=callback.message.id,
                    reply_markup=self.keyboard.reaction_buttons(sender_anon_id,
                                                                message_id,
                                                                toggled_emoji='هیچ ریاکشنی ندادی')
                )
            return

        # Update the reaction and send a notification
        await self.chat_manager.add_reaction(sender_user_id, message_id, emoji=reaction)
        await self.bot.set_message_reaction(
            chat_id=int(sender_user_id),
            message_id=int(message_id),
            reaction=[ReactionTypeEmoji(emoji=reaction)],
            is_big=False
        )
        # await self.bot.send_message(
        #     chat_id=sender_user_id,
        #     reply_to_message_id=int(message_id),
        #     text=get_response('texting.reaction.recipient'),
        #     parse_mode='HTML'
        # )

        await self.bot.edit_message_reply_markup(
            callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.reaction_buttons(sender_anon_id, message_id,
                                                        toggled_emoji=reaction)
        )
        await self.bot.answer_callback_query(callback.id,
                                                     get_response('texting.reaction.how_to_remove',))
                                                     
    async def _process_seen_callback(self, callback: CallbackQuery):
        """Process the seen callback."""
        sender_anon_id, message_id = callback.data.split('-')
        try:
            sender_id = await get_user_id(sender_anon_id)
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return

        if await self._check_bot_status(callback, sender_id):
            return

        await self.chat_manager.mark_message_seen(callback.from_user.id, int(callback.message.id))
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
        try:
            if not await self.blocker.validate_block_action(callback, sender_id):
                return
        except AttributeError:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('errors.user_not_found'), show_alert=True)
            return
        await self.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                reply_markup=self.keyboard.block_confirmation_buttons(sender_id, message_id)
            )

    async def _process_block_action_confirm(self, callback: CallbackQuery):
        """Process the block confirmation callback."""
        sender_id, message_id = callback.data.split('-')
        if not await self.blocker.validate_block_action(callback, sender_id):
            return
        await self.blocker.block_user(callback.message.chat.id, sender_id, callback, message_id)

    async def _process_block_action_cancel(self, callback: CallbackQuery):
        """Process the block cancellation callback."""
        sender_id, message_id = callback.data.split('-')
        await self.blocker.cancel_block(callback, message_id, sender_id)

    async def _process_unblock_shortcut_action(self, callback: CallbackQuery):
        """Process the unblock shortcut action callback."""
        blocked_id, message_id = callback.data.split('-')
        if not await self.blocker.is_user_blocked(blocked_id, callback.message.chat.id):
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.not_in_blocklist'),
                                                 show_alert=True)
            return
        await self.blocker.unblock_shortcut(callback, blocked_id, message_id)

    async def _process_add_note_request(self, callback: CallbackQuery):
        """Process the add note callback."""
        await self.chat_manager.close_chats(callback.message.chat.id)
        blocked_id = callback.data.split('-')[0]
        if not await self.blocker.is_user_blocked(blocked_id, callback.from_user.id):
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.not_in_blocklist'),
                                                 show_alert=True)
            return
        await self.blocker.add_note_request(callback, blocked_id)

    async def _process_read_note_request(self, callback: CallbackQuery):
        """Process the read note callback."""
        blocked_id = callback.data.split('-')[0]
        if not await self.blocker.is_user_blocked(blocked_id, callback.from_user.id):
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.not_in_blocklist'),
                                                 show_alert=True)
            return
        note = await self.blocker.get_block_note(callback, blocked_id)
        if note:
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.read_note', note=note),
                                                 show_alert=True)
        else:
            await self.bot.answer_callback_query(callback.id,
                                                 get_response('blocking.no_note'),
                                                 show_alert=True)

    async def _process_blocklist_page(self, callback: CallbackQuery):
        """Process the blocklist pagination callback."""
        blocker_id, page_str = callback.data.split("-")
        page = int(page_str)

        chat_id = callback.message.chat.id

        # Bind the user who pressed the button
        await self.user_manager.bind_user(chat_id)

        # Fetch fresh blocklist from DB
        user_data = await self.user_manager.fetch_user()
        blocklist = user_data.get("chatting", {}).get("blocklist", {})

        if not blocklist:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback.message.message_id,
                text=get_response("blocking.blocklist_empty")
            )
            return

        # Convert blocked user_ids → anon_ids
        blocklist_anon_ids = [anon_id async for anon_id in self.get_blocked_users_anon_ids()]

        # Regenerate keyboard for requested page
        await self.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=callback.message.message_id,
            reply_markup=self.keyboard.blocklist_buttons(
                blocker_id=blocker_id,
                blocked_list=blocklist_anon_ids,
                page=page
            )
        )

        # Always answer callback query to remove "loading..." spinner
        await self.bot.answer_callback_query(callback.id)

    async def _process_unblock_action(self, callback: CallbackQuery):
        """Process the unblock callback."""
        blocker_id, blocked_id = callback.data.split('-')
        blocker_id = await get_user_anon_id(callback.message.chat.id) if blocker_id == 'test' else blocker_id
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

        blocker_anon_id = await get_user_anon_id(callback.from_user.id)
        await self.blocker.unblock_user(callback, blocker_anon_id, blocked_id)

    async def _process_unblock_all_request(self, callback: CallbackQuery):
        """Process the unblock all request callback."""
        if await self._check_bot_status(callback, callback.from_user.id):
            return

        await self.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                reply_markup=self.keyboard.unblock_all_confirmation_buttons()
            )

    async def _process_unblock_all_request_cancel(self, callback: CallbackQuery):
        """Process the unblock all cancel callback."""
        if await self._check_bot_status(callback, callback.from_user.id):
            return

        await self.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                reply_markup=self.keyboard.blocklist_buttons(
                    blocker_id=await get_user_anon_id(callback.from_user.id),
                    blocked_list=[anon_id async for anon_id in self.blocker.get_blocked_users_anon_ids()]
                )
            )

    async def _process_unblock_all_request_confirm(self, callback: CallbackQuery):
        """Process the unblock all confirm callback."""
        if await self._check_bot_status(callback, callback.from_user.id):
            return

        await self.blocker.unblock_all_users(callback)

    async def _process_delete_message_callback(self, callback: CallbackQuery):
        """Process the delete message callback"""
        recipient_message_id, recipient_anon_id, sent_message_id, sent_announce_id = callback.data.split('-')

        await self.bot.delete_message(await get_user_id(recipient_anon_id), int(recipient_message_id))
        await self.bot.delete_message(callback.message.chat.id, int(sent_announce_id))
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)
        await self.bot.send_message(
            callback.message.chat.id,
            get_response('texting.tools.delete.didnt_send'),
            reply_to_message_id=sent_message_id,
            reply_markup=self.keyboard.main_buttons(),
            parse_mode='HTML')

    async def _process_change_nickname(self, callback: CallbackQuery):
        """Process the change nickname callback."""
        await self.chat_manager.close_chats(callback.message.chat.id, True)
        await NicknameManager(self.bot).set_nickname(callback.message)
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)

    async def _process_change_bio(self, callback: CallbackQuery):
        """Process the change bio callback."""
        await self.chat_manager.close_chats(callback.message.chat.id, True)
        await AccountManager.change_bio_request(self, callback)
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)

    async def _process_cancel(self, callback: CallbackQuery):
        """Process the cancel callback."""
        task = callback.data
        if task == "changing_nickname":
            await self.user_manager.bind_user(callback.from_user.id)
            await self.user_manager.toggle_flag('awaiting_nickname', False)
            await self.bot.edit_message_text(
                await AccountManager(self.bot).get_account_response(callback.message),
                callback.from_user.id,
                callback.message.id,
                parse_mode='HTML',
                reply_markup=self.keyboard.account_buttons()
            )

    async def _process_change_bot_status(self, callback: CallbackQuery):
        """Process the change bot status callback."""
        await SettingsManager(self.bot).change_bot_status(callback)

    async def _process_mark_message(self, callback: CallbackQuery):
        """Process the mark message callback."""
        sender_anon_id, message_id = callback.data.split('-')
        seen = await self.chat_manager.has_seen_message(user_id=callback.message.chat.id,
                                                  message_id=callback.message.id)

        original_text, is_caption = self._get_message_text_or_caption(callback)
        if not original_text:
            await self.bot.answer_callback_query(callback.id, "نمیتونم اینو نشون بزنم.")
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
        seen = await self.chat_manager.has_seen_message(user_id=callback.message.chat.id,
                                                  message_id=callback.message.id)
        marked = '📍 #نشان' in (callback.message.text or callback.message.caption or '')

        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=self.keyboard.recipient_option_buttons(sender_anon_id, message_id,
                                                                 is_seen=seen, is_marked=marked)
        )

    async def _process_revoke_link(self, callback: CallbackQuery):
        """Process the change link callback."""
        if await self.user_manager.is_bot_disabled(callback.from_user.id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.self.off'),
                show_alert=True
            )
            return

        # Check if revoked within the last 7 days
        last_revoke = await self.user_manager.get_metadata('last_revoke', 0)
        if last_revoke > 0 and (datetime.now().timestamp() - last_revoke) < 604800:
            await self.bot.answer_callback_query(
                callback.id,
                get_response('link.revoke_link.limit_exceeded'),
                show_alert=True
            )
            return

        await self.bot.send_message(callback.message.chat.id,
                                   get_response('link.revoke_link.confirm'),
                                   reply_markup=self.keyboard.regenarate_link_buttons(),
                                   parse_mode='HTML')

    async def _process_cancel_revoke_link(self, callback: CallbackQuery):
        """Process the cancel regenerate link callback."""
        await self.bot.answer_callback_query(callback.id,
                                             get_response('link.revoke_link.cancel'),
                                             show_alert=True)
        await self.bot.delete_message(callback.message.chat.id, callback.message.id)

    async def _process_confirm_revoke_link(self, callback: CallbackQuery):
        """Process the confirm regenerate link callback."""
        user_id = callback.message.chat.id
        link_manager = LinkManager(self.bot)
        await link_manager.revoke_link(callback.message)
        await self.bot.delete_message(user_id, callback.message.id)

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

    async def _check_bot_status(self, callback: CallbackQuery, user_id: int):
        """Verify if the bot status is disabled for the current user or the recipient."""
        if await self.user_manager.is_bot_disabled():
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.self.disabled'),
                show_alert=True
            )
            return True
        elif await self.user_manager.is_bot_disabled(user_id):
            await self.bot.answer_callback_query(
                callback.id,
                get_response('account.bot_status.recipient.disabled'),
                show_alert=True
            )
            return True
        return False

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
