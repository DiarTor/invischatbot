from bot.database.database import users_collection


def close_chats(user_id: int, reset_replying: bool = False) -> None:
    """
    Close all open chats for a user and optionally reset the replying state.
    :param user_id: User ID.
    :param reset_replying: Whether to reset replying state.
    """
    update_fields = {"chats.$[].open": False}
    if reset_replying:
        update_fields.update({"replying": False, "reply_target_message_id": "", "reply_target_user_id": ""})

    users_collection.update_one({"user_id": user_id}, {"$set": update_fields})


def add_seen_message(user_id, message_id: int):
    """
    Adds a message ID to the seen_messages array for a specific user.
    :param user_id: The ID of the user
    :param message_id: The ID of the message to mark as seen
    """
    users_collection.update_one(
        {
            "user_id": user_id
        },
        {
            "$addToSet": {
                "seen_messages": int(message_id)
            }
        }
    )


def get_seen_status(user_id, message_id: int):
    """
    Retrieve the seen status for the message from the user's document
    :param user_id: User ID of requester
    :param message_id: Message ID to check the seen status
    :return: Boolean indicating whether the message has been seen
    """
    # Query the database to get the 'seen_messages' for the user
    user_data = users_collection.find_one(
        {"user_id": user_id}
    )

    # Check if the 'seen_messages' array contains the given message_id
    if user_data:
        return int(message_id) in user_data.get('seen_messages', [])

    # If no data is found, assume the message has not been seen
    return False


def get_marked_status(text: str):
    if '#️⃣ #mark' in text:
        return True
    return False
