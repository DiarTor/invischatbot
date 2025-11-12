"""Manager for handling user account-related operations."""
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from telegram import CallbackQuery

from bot.common.data import UserDataManager, find_one
from bot.database.database import mongo
from bot.common.utils import convert_timestamp_to_date
from bot.common.keyboard import KeyboardMarkupGenerator
from bot.languages.response import get_response
from bot.common.validators import AccountValidator



class AccountManager:
    """Manager for handling user account-related operations."""
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.user_manager = UserDataManager()

    async def account(self, msg: Message):
        """ send the response text """
        await self.user_manager.bind_user(msg.chat.id)
        user_data = await self.user_manager.fetch_user()

        if user_data.get('flags', {}).get('is_bot_off', None):
            await self.bot.send_message(msg.chat.id, await self.get_account_response(msg),
                            parse_mode='HTML',
                            reply_markup=KeyboardMarkupGenerator().account_buttons(is_bot_off=True))
        else:
            await self.bot.send_message(msg.chat.id, await self.get_account_response(msg),
                                        parse_mode='HTML',
                                        reply_markup=KeyboardMarkupGenerator().account_buttons())
    
    async def change_bio_request(self, callback: CallbackQuery):
        """ return set bio response"""
        await self.user_manager.bind_user(callback.message.chat.id)
        await self.user_manager.toggle_flag('awaiting_bio', True)
        user_data = await self.user_manager.fetch_user()
        current_bio = user_data.get('profile', {}).get('bio', 'درحال حاضر بیوگرافی ندارید!')
        await self.bot.send_message(callback.message.chat.id,
                                    get_response('account.bio.ask_bio',
                                            current_bio=current_bio,),
                                            parse_mode='HTML',
                                            reply_markup=KeyboardMarkupGenerator().cancel_buttons())
    
    async def save_bio(self, msg: Message):
        """ save the new bio """
        new_bio = msg.text.strip()
        is_valid, validation_message = AccountValidator().validate_bio(new_bio)
        if not is_valid:
            await self.bot.send_message(
                msg.chat.id,
                f"{validation_message}",
            )
            return
        if new_bio == 'حذف':
            await self.user_manager.bind_user(msg.from_user.id)
            await self.user_manager.update_profile(**{"bio": ""})
            await self.user_manager.toggle_flag('awaiting_bio', False)
            await self.bot.send_message(msg.chat.id,
                                        get_response('account.bio.deleted'),
                                        parse_mode='HTML',
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())
        else:
            await self.user_manager.bind_user(msg.from_user.id)
            await self.user_manager.update_profile(**{"bio": new_bio})
            await self.user_manager.toggle_flag('awaiting_bio', False)
            await self.bot.send_message(msg.chat.id,
                                        get_response('account.bio.updated'),
                                        parse_mode='HTML',
                                        reply_markup=KeyboardMarkupGenerator().main_buttons())

    # async def referral(self, msg: Message):
    #     """
    #     Process the user invited by referral link.
    #     """
    #     referral_code_match = re.search(r"ref_(\w+)", msg.text)
    #     if not referral_code_match:
    #         return  # No valid referral code found

    #     referral_code = referral_code_match.group(1)
    #     inviter = users_collection.find_one({"id": referral_code})

    #     if inviter is None:
    #         return  # Stop execution if the ID is invalid

    #     invited = msg.chat.id

    #     if not inviter:
    #         return  # Stop execution if inviter is not found

    #     if fetch_user_data_by_id(invited).get('referred'):
    #         await self.bot.send_message(invited, get_response('account.referral.referred'))
    #         return

    #     if inviter.get('user_id') == invited:
    #         await self.bot.send_message(invited, get_response('account.referral.invite_self'))
    #         return

    #     if invited in inviter.get('referrals', []):
    #         return  # Already referred by the same inviter, do nothing

    #     update_user_fields(invited, {'referred': True, 'referred_by': referral_code})
    #     update_user_fields(inviter.get("user_id"), "referrals", get_user_anon_id(invited),
    #     push=True)

    @staticmethod
    async def get_account_response(msg: Message):
        """ return the response text"""
        user_data = await find_one(mongo.users_collection, {'user_id': msg.chat.id})
        joined_at = convert_timestamp_to_date(user_data['metadata'].get('joined_at', 0))
        # referrals = len(user_data.get('referrals'))
        response_data = {
            'anon_id': user_data['anon_id'],
            'nickname': user_data['profile'].get('nickname', ''),
            'joined_at': joined_at,
            # 'referrals': referrals
            'bio': user_data['profile'].get('bio', 'درحال حاضر بیوگرافی ندارید!')
        }
        return get_response('account.show', **response_data)
