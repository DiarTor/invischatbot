from datetime import datetime

import jdatetime


def convert_timestamp_to_date(timestamp, show="date", calendar_type="gregorian"):
    """
    Convert a timestamp to Jalali (Persian) or Gregorian date and time format.

    Parameters:
    - timestamp: The input timestamp (in seconds since epoch).
    - show: Determines the format of the output. Options are:
        - "date": Show only the date (e.g., 1403/01/01 or 2024/01/01)
        - "time": Show only the time (e.g., 14:30:00)
        - "datetime": Show both date and time (e.g., 1403/01/01 14:30:00 or 2024/01/01 14:30:00)
    - calendar_type: The calendar format to use. Options are:
        - "jalali": Use the Jalali (Persian) calendar
        - "gregorian": Use the Gregorian calendar

    Returns:
    - A formatted string according to the selected `show` and `calendar_type` options.
    """
    # Convert the timestamp to the appropriate datetime object
    if calendar_type == "jalali":
        date_time = jdatetime.datetime.fromtimestamp(timestamp)
    elif calendar_type == "gregorian":
        date_time = datetime.fromtimestamp(timestamp)
    else:
        raise ValueError("Invalid `calendar_type`. Choose from 'jalali' or 'gregorian'.")

    # Format according to the `show` parameter
    if show == "date":
        return date_time.strftime("%Y/%m/%d")
    elif show == "time":
        return date_time.strftime("%H:%M:%S")
    elif show == "datetime":
        return date_time.strftime("%Y/%m/%d %H:%M:%S")
    else:
        raise ValueError("Invalid `show` option. Choose from 'date', 'time', or 'datetime'.")
