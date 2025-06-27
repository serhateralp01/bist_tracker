# backend/utils/portfolio_calculator.py

from datetime import datetime, date
from collections import defaultdict
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from .. import models

def calculate_portfolio_value(transactions, prices):
    holdings = defaultdict(float)
    cash = 0

    for t in transactions:
        symbol = t.symbol.upper() if t.symbol else None
        qty = t.quantity
        price = t.price or 0

        if t.type == "buy" and symbol:
            holdings[symbol] += qty
            cash -= qty * price
        elif t.type == "sell" and symbol:
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

def calculate_cost_basis_fifo(db: Session, symbol: str, current_quantity: float) -> Tuple[float, float]:
    """
    Calculate cost basis using FIFO (First In, First Out) method
    Returns: (total_cost_basis, average_purchase_price)
    """
    # Get all transactions for this symbol, ordered by date
    transactions = db.query(models.Transaction).filter(
        models.Transaction.symbol == symbol
    ).order_by(models.Transaction.date).all()
    
    # Track purchases (FIFO queue)
    purchase_queue = []  # [(quantity, price, date), ...]
    total_cost_basis = 0.0
    remaining_quantity = current_quantity
    
    for tx in transactions:
        if tx.type == "buy":
            purchase_queue.append((tx.quantity, tx.price or 0, tx.date))
        elif tx.type == "sell":
            # Remove from oldest purchases first (FIFO)
            sell_quantity = tx.quantity
            while sell_quantity > 0 and purchase_queue:
                oldest_qty, oldest_price, oldest_date = purchase_queue.pop(0)
                if oldest_qty <= sell_quantity:
                    # Sell entire oldest batch
                    sell_quantity -= oldest_qty
                else:
                    # Partially sell oldest batch
                    purchase_queue.insert(0, (oldest_qty - sell_quantity, oldest_price, oldest_date))
                    sell_quantity = 0
        elif tx.type == "split":
            # Adjust all purchase quantities for split, prices adjust proportionally
            # For stock splits, quantity increases but total value stays same
            if purchase_queue:
                # For splits, we add new shares to holdings but adjust price basis
                # tx.quantity represents the new shares added
                total_current_qty = sum(p[0] for p in purchase_queue)
                if total_current_qty > 0:
                    split_ratio = 1 + (tx.quantity / total_current_qty)
                    purchase_queue = [(qty * split_ratio, price / split_ratio, date) 
                                    for qty, price, date in purchase_queue]
    
    # Calculate cost basis from remaining purchases
    for qty, price, date in purchase_queue:
        if remaining_quantity <= 0:
            break
        
        quantity_to_use = min(qty, remaining_quantity)
        total_cost_basis += quantity_to_use * price
        remaining_quantity -= quantity_to_use
    
    # Calculate average purchase price
    avg_price = total_cost_basis / current_quantity if current_quantity > 0 else 0
    
    return round(total_cost_basis, 2), round(avg_price, 2)

def get_user_performance_since_purchase(db: Session, symbol: str, current_price: float = None) -> Dict[str, float]:
    """
    Calculate actual user performance since first purchase of this stock
    Can accept a pre-fetched current_price for optimization.
    """
    # If price isn't provided, fetch it.
    if current_price is None:
        from .stock_fetcher import get_latest_price
        current_price = get_latest_price(symbol) or 0

    # Get first purchase date
    first_buy = db.query(models.Transaction).filter(
        models.Transaction.symbol == symbol,
        models.Transaction.type == "buy"
    ).order_by(models.Transaction.date).first()
    
    if not first_buy:
        return {"error": "No purchase found for this symbol"}
    
    first_purchase_date = first_buy.date
    
    # Get current holdings and cost basis
    holdings = get_current_holdings_with_quantities(db)
    if symbol not in holdings:
        return {"error": "Stock not currently held"}
    
    current_quantity = holdings[symbol]
    cost_basis, avg_purchase_price = calculate_cost_basis_fifo(db, symbol, current_quantity)
    
    # Get current value with the provided or fetched price
    current_value = current_quantity * current_price
    
    # Calculate performance metrics
    total_return = current_value - cost_basis
    return_percentage = (total_return / cost_basis * 100) if cost_basis > 0 else 0
    
    # Calculate days held
    days_held = (datetime.now().date() - first_purchase_date).days
    
    # Annualized return
    if days_held > 0:
        annualized_return = ((current_value / cost_basis) ** (365 / days_held) - 1) * 100 if cost_basis > 0 else 0
    else:
        annualized_return = 0
    
    return {
        "symbol": symbol,
        "first_purchase_date": first_purchase_date.strftime("%Y-%m-%d"),
        "days_held": days_held,
        "current_quantity": current_quantity,
        "cost_basis": cost_basis,
        "average_purchase_price": avg_purchase_price,
        "current_price": current_price,
        "current_value": round(current_value, 2),
        "total_return": round(total_return, 2),
        "return_percentage": round(return_percentage, 2),
        "annualized_return": round(annualized_return, 2)
    }

def get_current_holdings(db: Session) -> List[str]:
    """
    Get list of stock symbols currently held in portfolio (quantity > 0)
    """
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