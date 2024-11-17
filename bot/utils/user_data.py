from bot.utils.database import users_collection


def close_existing_chats(user_id: int):
    """

    :param user_id: user id
    :return:
    """
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"replying": False, "reply_target_message_id": "", "reply_target_user_id": "",
                  "chats.$[].open": False}}  # Close all open chats, reset replying
    )


def reset_replying_state(user_id: int):
    """Reset the replying state for the user."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"replying": False, "reply_target_message_id": "", "reply_target_user_id": ""}}
        # Clear reply state
    )


def get_user(user_id: int):
    return users_collection.find_one({"user_id": user_id})


def is_user_blocked(sender_id: str, recipient_id: int) -> bool:
    """

    :param sender_id: anny id
    :param recipient_id: user id
    :return:
    """
    sender_data = users_collection.find_one({"id": sender_id})
    recipient_data = users_collection.find_one({"user_id": recipient_id})
    return recipient_data and (
            sender_data['id'] in recipient_data.get('blocklist', []) or
            recipient_data['id'] in sender_data.get('blocklist', [])
    )
