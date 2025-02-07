import re

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.utils.database import users_collection
from bot.utils.date import convert_timestamp_to_date
from bot.utils.keyboard import KeyboardMarkupGenerator
from bot.utils.language import get_response
from bot.utils.user_data import get_user_by_id, update_user_field, get_user_anny_id, update_user_fields


class AccountManager:
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot

    async def account(self, msg: Message):
        """ send the response text"""
        user_data = get_user_by_id(msg.chat.id)
        joined_at = convert_timestamp_to_date(user_data['joined_at'])
        referrals = len(user_data.get('referrals'))
        if user_data.get('is_bot_off'):
            await self.bot.send_message(msg.chat.id, get_response('account.show', user_data['id'],
                                                                  user_data['nickname'], joined_at, referrals),
                                        parse_mode='Markdown',
                                        reply_markup=KeyboardMarkupGenerator().account_buttons(is_bot_off=True))
        else:
            await self.bot.send_message(msg.chat.id, get_response('account.show', user_data['id'],
                                                                  user_data['nickname'], joined_at, referrals),
                                        parse_mode='Markdown',
                                        reply_markup=KeyboardMarkupGenerator().account_buttons())

    async def referral(self, msg: Message):
        """
        Process the user invited by referral link.
        """
        referral_code_match = re.search(r"ref_(\w+)", msg.text)
        if not referral_code_match:
            return  # No valid referral code found

        referral_code = referral_code_match.group(1)
        inviter = users_collection.find_one({"id": referral_code})

        if inviter is None:
            return  # Stop execution if the ID is invalid

        invited = msg.chat.id

        if not inviter:
            return  # Stop execution if inviter is not found

        if get_user_by_id(invited).get('referred'):
            await self.bot.send_message(invited, get_response('account.referral.referred'))
            return

        if inviter.get('user_id') == invited:
            await self.bot.send_message(invited, get_response('account.referral.invite_self'))
            return

        if invited in inviter.get('referrals', []):
            return  # Already referred by the same inviter, do nothing

        update_user_fields(invited, {'referred': True, 'referred_by': referral_code})
        update_user_field(inviter.get("user_id"), "referrals", get_user_anny_id(invited), push=True)

    @staticmethod
    def get_account_response(msg: Message):
        """ return the response text"""
        user_data = get_user_by_id(msg.chat.id)
        joined_at = convert_timestamp_to_date(user_data['joined_at'])
        referrals = len(user_data.get('referrals'))
        return get_response('account.show', user_data['id'],
                            user_data['nickname'], joined_at, referrals)
