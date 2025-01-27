import pytz
from datetime import datetime
from django.utils.timezone import make_aware

def convert_to_utc(date, time, timezone_str):
    """
    Converts a date and time with a specific timezone to UTC.
    """
    # Combine date and time into a datetime object
    local_time = datetime.combine(date, time)
    
    # Localize to the given timezone
    local_tz = pytz.timezone(timezone_str)
    localized_time = local_tz.localize(local_time)

    # Convert to UTC
    utc_time = localized_time.astimezone(pytz.UTC)
    return utc_time
