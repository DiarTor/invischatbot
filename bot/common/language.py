from languages.dictionary import translations


def get_response(address: str, locale: str = 'fa', **kwargs) -> str | None:
    # Check if the locale exists in translations, else default to 'fa'
    data = translations.get(locale, translations.get('fa', {}))
    if not data:
        print(f"Error: Locale '{locale}' not found in the translations dictionary.")
        return None

    keys = address.split('.')

    # Traverse the dictionary using the address
    for key in keys:
        if not isinstance(data, dict):
            print(f"Error: {key} path does not lead to a valid dictionary.")
            return None
        data = data.get(key)
        if data is None:
            print(f"Error: Key '{key}' not found in the dictionary.")
            return None

    # Format and return the response if data is a string
    if isinstance(data, str):
        try:
            return data.format(**kwargs)  # Format using named placeholders
        except KeyError as e:
            missing_key = str(e).strip("'")
            print(f"Error: Missing placeholder '{missing_key}' in the format string.")
            return f"Missing placeholder: {missing_key}"

    print(f"Error: Final data is not a string. Found: {type(data)}")
    return None
