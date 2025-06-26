# backend/utils/portfolio_calculator.py

from datetime import datetime
from collections import defaultdict

def calculate_portfolio_value(transactions, prices):
    holdings = defaultdict(float)
    cash = 0

    for t in transactions:
        symbol = t.symbol.upper()
        qty = t.quantity
        price = t.price or 0

        if t.type == "buy":
            holdings[symbol] += qty
            cash -= qty * price
        elif t.type == "sell":
            holdings[symbol] -= qty
            cash += qty * price
        elif t.type == "deposit":
            cash += qty
        elif t.type == "withdrawal":
            cash -= qty

    total_value = cash
    for symbol, qty in holdings.items():
        if symbol in prices:
            total_value += qty * prices[symbol]

    return {
        "date": datetime.today().strftime("%Y-%m-%d"),
        "holdings": dict(holdings),
        "cash": round(cash, 2),
        "total_value": round(total_value, 2)
    }