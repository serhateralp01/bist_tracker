import re
from datetime import datetime, date
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
    Parses a dividend or stock split message.
    Handles both dated formats and undated bank message formats.
    """
    
    # NEW: Handle actual bank format without dates (user's format)
    # Pattern: "Degerli Musterimiz, TCELL.E senedi %154.55 temettu vermis, hesaplariniza yansitilmistir"
    bank_dividend_match = re.search(r"Degerli\s+Musterimiz,\s+(\w+)\.E\s+senedi\s+%([\d\.]+)\s+temett[uü]\s+vermi[sş]", message, re.IGNORECASE)
    if bank_dividend_match:
        symbol, percentage_str = bank_dividend_match.groups()
        return {
            "type": "dividend",
            "date": date.today(),  # Use today's date since bank doesn't provide date
            "symbol": symbol,
            "percentage": float(percentage_str)
        }
    
    # NEW: Handle actual bank format for capital increase
    # Pattern: "Degerli Musterimiz, AEFES.E senedi %900 bedelsiz sermaye artirimi yapmis, hesaplariniza yansitilmistir"
    bank_split_match = re.search(r"Degerli\s+Musterimiz,\s+(\w+)\.E\s+senedi\s+%([\d\.]+)\s+bedelsiz\s+sermaye\s+artirimi\s+yapmi[sş]", message, re.IGNORECASE)
    if bank_split_match:
        symbol, percentage_str = bank_split_match.groups()
        percentage = float(percentage_str)
        # Convert percentage to ratio (e.g., 900% = 9 additional shares per 1 share = 10:1 total ratio)
        ratio = 1 + (percentage / 100.0)
        return {
            "type": "split",
            "date": date.today(),  # Use today's date since bank doesn't provide date
            "symbol": symbol,
            "ratio": ratio,
            "percentage": percentage
        }

    # LEGACY: Handle dated format for backward compatibility
    # Regex for dividend with DD.MM.YYYY date - handle both temettu and temettü
    dividend_match = re.search(r"(\d{2}\.\d{2}\.\d{4}):.* (\w+)\.E.*?%([\d\.]+)\s+temett[uü]", message, re.IGNORECASE)
    if dividend_match:
        date_str, symbol, percentage_str = dividend_match.groups()
        return {
            "type": "dividend",
            "date": datetime.strptime(date_str, "%d.%m.%Y").date(),
            "symbol": symbol,
            "percentage": float(percentage_str)
        }

    # LEGACY: Handle dated format for stock split/bonus shares
    split_match = re.search(r"(\d{2}\.\d{2}\.\d{4}):.*? (\w+)\.E.*?%(\d+(?:\.\d+)?) bedelsiz.*?artirimi", message, re.IGNORECASE)
    if split_match:
        date_str, symbol, percentage_str = split_match.groups()
        percentage = float(percentage_str)
        # Convert percentage to ratio (e.g., 1000% = 10 additional shares per 1 share = 11:1 total ratio)
        ratio = 1 + (percentage / 100.0)
        return {
            "type": "split",
            "date": datetime.strptime(date_str, "%d.%m.%Y").date(),
            "symbol": symbol,
            "ratio": ratio,
            "percentage": percentage
        }

    # LEGACY: Fallback regex for older format without 'artirimi'
    split_match_old = re.search(r"(\d{2}\.\d{2}\.\d{4}):.*? (\w+)\.E.*?%(\d+(?:\.\d+)?) bedelsiz", message, re.IGNORECASE)
    if split_match_old:
        date_str, symbol, percentage_str = split_match_old.groups()
        percentage = float(percentage_str)
        ratio = 1 + (percentage / 100.0)
        return {
            "type": "split",
            "date": datetime.strptime(date_str, "%d.%m.%Y").date(),
            "symbol": symbol,
            "ratio": ratio,
            "percentage": percentage
        }

    return None 