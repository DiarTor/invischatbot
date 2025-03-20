from telebot.async_telebot import AsyncTeleBot

from bot.database.database import users_collection


def is_bot_status_off(user_id: str | int):
    if users_collection.find_one({"user_id": user_id}).get('is_bot_off', False):
        return True
    return False


async def is_subscribed_to_channel(bot: AsyncTeleBot, user_id: int):
    """
    Check if the user is subscribed to the channel.
    :param user_id: the user telegram user id
    :param bot: An instance Of telebot.TeleBot
    :return: True if the user is subscribed to the channel, False otherwise
    """
    channel_id = -1002456307928
    chat_member = await bot.get_chat_member(chat_id=int(channel_id), user_id=user_id)
    if chat_member.status in ["member", "administrator", "creator"]:
        return True
    return False
