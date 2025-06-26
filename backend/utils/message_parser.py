import re
from datetime import date

def parse_message(text: str):
    """Parse capital increase, rights issue, and dividend messages"""
    # Temettü mesajı yakalama
    temettu_match = re.search(r"(\w+)\.E senedi %([\d\.]+) temettu", text, re.IGNORECASE)
    if temettu_match:
        symbol = temettu_match.group(1)
        percentage = float(temettu_match.group(2))
        return {
            "type": "dividend",
            "symbol": symbol,
            "rate": percentage / 100,
            "date": date.today().isoformat(),
            "note": f"%{percentage} temettü"
        }

    # Bedelsiz sermaye artırımı mesajı yakalama
    bedelsiz_match = re.search(r"(\w+)\.E senedi %([\d\.]+) bedelsiz sermaye artirimi", text, re.IGNORECASE)
    if bedelsiz_match:
        symbol = bedelsiz_match.group(1)
        percentage = float(bedelsiz_match.group(2))
        return {
            "type": "capital_increase",
            "symbol": symbol,
            "rate": percentage / 100,  # Convert percentage to decimal
            "date": date.today().isoformat(),
            "note": f"%{percentage} bedelsiz sermaye artırımı"
        }

    # Bedelli sermaye artırımı mesajı yakalama
    bedelli_match = re.search(r"(\w+)\.E senedi %([\d\.]+) bedelli sermaye artirimi", text, re.IGNORECASE)
    if bedelli_match:
        symbol = bedelli_match.group(1)
        percentage = float(bedelli_match.group(2))
        return {
            "type": "rights_issue",
            "symbol": symbol,
            "rate": percentage / 100,
            "date": date.today().isoformat(),
            "note": f"%{percentage} bedelli sermaye artırımı"
        }

    return None



def parse_and_log_message(text: str):
    # Temettü mesajı yakalama
    temettu_match = re.search(r"(\w+)\.E senedi %([\d\.]+) temettu", text, re.IGNORECASE)
    if temettu_match:
        symbol = temettu_match.group(1)
        percentage = float(temettu_match.group(2))
        return {
            "type": "dividend",
            "symbol": symbol,
            "percentage": percentage,
            "date": date.today().isoformat(),
            "note": f"%{percentage} temettü"
        }

    # Bedelsiz sermaye artırımı mesajı yakalama
    bedelsiz_match = re.search(r"(\w+)\.E senedi %([\d\.]+) bedelsiz sermaye artirimi", text, re.IGNORECASE)
    if bedelsiz_match:
        symbol = bedelsiz_match.group(1)
        percentage = float(bedelsiz_match.group(2))
        return {
            "type": "capital_increase",
            "symbol": symbol,
            "percentage": percentage,
            "date": date.today().isoformat(),
            "note": f"%{percentage} bedelsiz"
        }

    raise ValueError("Message could not be parsed.")