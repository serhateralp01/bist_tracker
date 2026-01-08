import re
from datetime import date

def parse_message(text: str):
    """Parse buy/sell transactions, capital increase, rights issue, and dividend messages"""
    
    # 1. BUY TRANSACTION PATTERNS
    # Pattern 1: "SYMBOL hissesinden X adet hisse Y.Z TL fiyattan alinmistir"
    buy_match1 = re.search(r"(\w+)\s+hissesinden\s+([\d\.]+)\s+adet\s+hisse\s+([\d\.]+)\s+TL\s+fiyattan\s+alinmistir", text, re.IGNORECASE)
    if buy_match1:
        symbol = buy_match1.group(1).upper()
        quantity = float(buy_match1.group(2))
        price = float(buy_match1.group(3))
        return {
            "type": "buy",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "date": date.today().isoformat(),
            "note": f"Buy {quantity} shares at {price} TL"
        }
    
    # Pattern 2: "SYMBOL X adet Y.Z fiyattan alim islemi gerceklestirilmistir"
    buy_match2 = re.search(r"(\w+)\s+([\d\.]+)\s+adet\s+([\d\.]+)\s+fiyattan\s+alim\s+islemi\s+gerceklestirilmistir", text, re.IGNORECASE)
    if buy_match2:
        symbol = buy_match2.group(1).upper()
        quantity = float(buy_match2.group(2))
        price = float(buy_match2.group(3))
        return {
            "type": "buy",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "date": date.today().isoformat(),
            "note": f"Buy {quantity} shares at {price} TL"
        }
    
    # 2. SELL TRANSACTION PATTERNS  
    # Pattern 1: "SYMBOL hissesinden X adet hisse Y.Z TL fiyattan satilmistir"
    sell_match1 = re.search(r"(\w+)\s+hissesinden\s+([\d\.]+)\s+adet\s+hisse\s+([\d\.]+)\s+TL\s+fiyattan\s+satilmistir", text, re.IGNORECASE)
    if sell_match1:
        symbol = sell_match1.group(1).upper()
        quantity = float(sell_match1.group(2))
        price = float(sell_match1.group(3))
        return {
            "type": "sell",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "date": date.today().isoformat(),
            "note": f"Sell {quantity} shares at {price} TL"
        }
    
    # Pattern 2: "SYMBOL X adet Y.Z fiyattan satis islemi gerceklestirilmistir"
    sell_match2 = re.search(r"(\w+)\s+([\d\.]+)\s+adet\s+([\d\.]+)\s+fiyattan\s+satis\s+islemi\s+gerceklestirilmistir", text, re.IGNORECASE)
    if sell_match2:
        symbol = sell_match2.group(1).upper()
        quantity = float(sell_match2.group(2))
        price = float(sell_match2.group(3))
        return {
            "type": "sell",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "date": date.today().isoformat(),
            "note": f"Sell {quantity} shares at {price} TL"
        }

    # 3. DIVIDEND MESSAGES (Legacy support - should use event_parser for new messages)
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

    # 4. CAPITAL INCREASE MESSAGES (Legacy support)
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

    # 5. RIGHTS ISSUE MESSAGES (Legacy support)
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
    """Legacy function - use parse_message instead"""
    result = parse_message(text)
    if result:
        return result
    raise ValueError("Message could not be parsed.")