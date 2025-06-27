# backend/utils/portfolio_calculator.py

from datetime import datetime
from collections import defaultdict
from typing import List, Dict
from sqlalchemy.orm import Session

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

def get_current_holdings(db: Session) -> List[str]:
    """
    Get list of stock symbols currently held in portfolio (quantity > 0)
    """
    from backend import models
    
    transactions = db.query(models.Transaction).all()
    holdings = defaultdict(float)
    
    for tx in transactions:
        if tx.symbol and tx.quantity:
            if tx.type == 'buy':
                holdings[tx.symbol] += tx.quantity
            elif tx.type == 'sell':
                holdings[tx.symbol] -= tx.quantity
            elif tx.type == 'split':
                holdings[tx.symbol] += tx.quantity
    
    # Return only symbols with positive quantities
    return [symbol for symbol, quantity in holdings.items() if quantity > 0]

def get_current_holdings_with_quantities(db: Session) -> Dict[str, float]:
    """
    Get current holdings with their quantities
    """
    from backend import models
    
    transactions = db.query(models.Transaction).all()
    holdings = defaultdict(float)
    
    for tx in transactions:
        if tx.symbol and tx.quantity:
            if tx.type == 'buy':
                holdings[tx.symbol] += tx.quantity
            elif tx.type == 'sell':
                holdings[tx.symbol] -= tx.quantity
            elif tx.type == 'split':
                holdings[tx.symbol] += tx.quantity
    
    # Return only symbols with positive quantities
    return {symbol: quantity for symbol, quantity in holdings.items() if quantity > 0}