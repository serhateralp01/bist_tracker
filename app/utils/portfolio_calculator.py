from sqlalchemy.orm import Session
from app import models
from collections import defaultdict
from datetime import datetime, date

def calculate_portfolio_value(transactions, current_prices):
    """
    Calculates the current portfolio value based on transactions and current prices.
    """
    portfolio = defaultdict(float)
    total_value = 0.0

    # Calculate share counts
    for tx in transactions:
        if tx.type == "buy":
            portfolio[tx.symbol] += tx.quantity
        elif tx.type == "sell":
            portfolio[tx.symbol] -= tx.quantity
        elif tx.type == "split":
            portfolio[tx.symbol] += tx.quantity

    # Calculate value
    portfolio_details = []
    for symbol, quantity in portfolio.items():
        if quantity > 0:
            price = current_prices.get(symbol, 0.0)
            value = quantity * price
            total_value += value
            portfolio_details.append({
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "value": value
            })

    return {
        "total_value": total_value,
        "holdings": portfolio_details
    }

def get_current_holdings(db: Session):
    """Returns a list of symbols currently held in the portfolio."""
    transactions = db.query(models.Transaction).all()
    holdings = defaultdict(float)

    for tx in transactions:
        if tx.type == "buy":
            holdings[tx.symbol] += tx.quantity
        elif tx.type == "sell":
            holdings[tx.symbol] -= tx.quantity
        elif tx.type == "split":
            holdings[tx.symbol] += tx.quantity

    return [symbol for symbol, quantity in holdings.items() if quantity > 0.001]

def get_current_holdings_with_quantities(db: Session):
    """Returns a dictionary of symbols and their current quantities."""
    transactions = db.query(models.Transaction).all()
    holdings = defaultdict(float)

    for tx in transactions:
        if tx.type == "buy":
            holdings[tx.symbol] += tx.quantity
        elif tx.type == "sell":
            holdings[tx.symbol] -= tx.quantity
        elif tx.type == "split":
            holdings[tx.symbol] += tx.quantity

    return {symbol: quantity for symbol, quantity in holdings.items() if quantity > 0.001}

def calculate_cost_basis_fifo(db: Session, symbol: str, current_quantity: float):
    """
    Calculates the cost basis using FIFO (First-In, First-Out) method.
    Returns (total_cost, average_cost_per_share)
    """
    transactions = db.query(models.Transaction).filter(
        models.Transaction.symbol == symbol
    ).order_by(models.Transaction.date).all()

    buy_queue = [] # List of (quantity, price, date)

    for tx in transactions:
        if tx.type == "buy":
            buy_queue.append({"qty": tx.quantity, "price": tx.price, "date": tx.date})
        elif tx.type == "sell":
            sell_qty = tx.quantity
            while sell_qty > 0 and buy_queue:
                batch = buy_queue[0]
                if batch["qty"] > sell_qty:
                    batch["qty"] -= sell_qty
                    sell_qty = 0
                else:
                    sell_qty -= batch["qty"]
                    buy_queue.pop(0)
        elif tx.type == "split":
            # For splits, we need to adjust all previous batches
            # Assuming simple split where quantity increases and price decreases
            # We need to find the split ratio relative to current holdings
            # This is complex because we don't store the ratio directly in the transaction for historical splits
            # But usually split transaction has quantity = existing_shares * (ratio - 1)
            # So new total = existing + quantity
            pass
            # Note: A proper split implementation would need the ratio.
            # For now, we'll assume the quantity in buy_queue matches the split logic
            # if we were to replay it perfectly, but simple adjustment:
            # If we just added shares, we effectively lower the cost basis per share
            # But FIFO logic usually tracks lots.
            # Simplified approach: Just adding zero cost shares to the queue?
            # Or adjusting existing batches?
            # Let's try adding zero-cost shares for the split amount
            # buy_queue.append({"qty": tx.quantity, "price": 0.0, "date": tx.date})
            # Actually, standard way is to adjust price and quantity of existing lots.

            # Re-calculating ratio from transaction might be hard without knowing total at that point.
            # But let's assume we can add them as 0 cost basis for now as a simplification,
            # effectively averaging down.
            if tx.quantity > 0:
                 buy_queue.append({"qty": tx.quantity, "price": 0.0, "date": tx.date})


    # Calculate cost of remaining shares
    total_cost = 0.0
    remaining_qty = 0.0

    # We only want to sum up to current_quantity (in case there's a mismatch or rounding)
    needed = current_quantity

    for batch in buy_queue:
        if needed <= 0:
            break

        take = min(needed, batch["qty"])
        total_cost += take * batch["price"]
        needed -= take
        remaining_qty += take

    avg_cost = total_cost / remaining_qty if remaining_qty > 0 else 0.0

    return total_cost, avg_cost

def get_user_performance_since_purchase(db: Session, symbol: str, current_price: float = None):
    """
    Calculates performance metrics for a specific stock based on user's purchase history.
    """
    # 1. Get current holdings and quantity
    holdings = get_current_holdings_with_quantities(db)
    quantity = holdings.get(symbol, 0)

    if quantity <= 0:
        return {"error": "Stock not currently held"}

    # 2. Calculate Cost Basis (FIFO)
    cost_basis, avg_purchase_price = calculate_cost_basis_fifo(db, symbol, quantity)

    # 3. Get Current Price if not provided
    if current_price is None:
        from .stock_fetcher import get_latest_price
        current_price = get_latest_price(symbol)

    if not current_price:
        return {"error": "Could not fetch current price"}

    # 4. Calculate Values
    current_value = quantity * current_price
    gain_loss_amount = current_value - cost_basis
    gain_loss_percent = (gain_loss_amount / cost_basis * 100) if cost_basis > 0 else 0

    # 5. Get First Purchase Date for Days Held
    first_purchase = db.query(models.Transaction).filter(
        models.Transaction.symbol == symbol,
        models.Transaction.type == 'buy'
    ).order_by(models.Transaction.date).first()

    days_held = 0
    if first_purchase:
        days_held = (date.today() - first_purchase.date).days

    # 6. Calculate Annualized Return
    annualized_return = 0
    if days_held > 0:
        # Simple CAGR formula: (End Value / Start Value)^(365/days) - 1
        # Using cost basis as start value
        if cost_basis > 0 and current_value > 0:
            try:
                annualized_return = ((current_value / cost_basis) ** (365 / days_held) - 1) * 100
            except:
                annualized_return = 0

    return {
        "symbol": symbol,
        "quantity": quantity,
        "cost_basis": cost_basis,
        "current_value": current_value,
        "average_purchase_price": avg_purchase_price,
        "current_price": current_price,
        "return_amount": gain_loss_amount,
        "return_percentage": gain_loss_percent,
        "first_purchase_date": first_purchase.date.strftime("%Y-%m-%d") if first_purchase else None,
        "days_held": days_held,
        "annualized_return": annualized_return
    }
