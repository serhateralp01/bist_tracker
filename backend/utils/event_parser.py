import re
from datetime import datetime
import locale

# Dictionary to map English month abbreviations to month numbers.
# This avoids all locale-related parsing issues.
month_map = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

def parse_date_robustly(date_str: str) -> datetime.date:
    """Parses a 'mon day year' string without depending on locale."""
    parts = date_str.lower().split()
    month_num = month_map.get(parts[0][:3])
    if not month_num:
        raise ValueError(f"Unknown month in date string: {date_str}")
    
    day = int(parts[1])
    year_two_digit = int(parts[2])
    # Assuming the century is 2000
    year = 2000 + year_two_digit

    return datetime(year, month_num, day).date()

def parse_event_message(message: str):
    """
    Parses a dividend or stock split message with a DD.MM.YYYY date format.
    """
    # Regex for dividend with DD.MM.YYYY date
    dividend_match = re.search(r"(\d{2}\.\d{2}\.\d{4}):.*? (\w+)\.E.*?%([\d\.]+) temettu", message, re.IGNORECASE)
    if dividend_match:
        date_str, symbol, percentage_str = dividend_match.groups()
        return {
            "type": "dividend",
            "date": datetime.strptime(date_str, "%d.%m.%Y").date(),
            "symbol": symbol,
            "percentage": float(percentage_str)
        }

    # Regex for stock split with DD.MM.YYYY date
    split_match = re.search(r"(\d{2}\.\d{2}\.\d{4}):.*? (\w+)\.E.*?%([\d\.]+) bedelsiz", message, re.IGNORECASE)
    if split_match:
        date_str, symbol, percentage_str = split_match.groups()
        ratio = 1 + (float(percentage_str) / 100.0)
        return {
            "type": "split",
            "date": datetime.strptime(date_str, "%d.%m.%Y").date(),
            "symbol": symbol,
            "ratio": ratio
        }

    return None 