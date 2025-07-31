from datetime import datetime

def convert_long_to_date(timestamp_ms):
    try:
        # Try to convert and format the timestamp
        timestamp_sec = int(timestamp_ms) / 1000
        dt = datetime.fromtimestamp(timestamp_sec)
    except (ValueError, TypeError, OSError):
        # If error, fallback to current time
        dt = datetime.now()
    return dt.strftime('%-m/%-d/%Y')  # Unix-based systems (Linux, macOS)

# For Windows systems, use the following line instead:
# return dt.strftime('%#m/%#d/%Y')
