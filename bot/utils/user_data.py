from bot.utils.database import users_collection


def close_existing_chats(user_id: int):
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
