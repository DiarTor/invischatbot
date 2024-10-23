from languages.iran import persian


def get_response(address: str, *args) -> str | None:
    """
    Retrieves and formats a text string from a nested dictionary based on the given address.
    :param address: A dot-separated string indicating the path to the desired key in the nested dictionary.
    :param args: Additional arguments to format the retrieved string.
    :return: The formatted string if the address leads to a string value, otherwise None.
    """
    keys = address.split('.')
    data = persian
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key, {})
    if isinstance(data, str):
        return data.format(*args)
    return None
