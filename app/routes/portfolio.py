from flask import Blueprint, render_template, request, jsonify
from app import db, models
from app.utils.portfolio_calculator import get_current_holdings_with_quantities, calculate_cost_basis_fifo
from app.utils.stock_fetcher import get_latest_price
from app.utils.currency_fetcher import get_latest_eur_try_rate

bp = Blueprint('portfolio', __name__)

@bp.route('/portfolio')
def index():
    try:
        holdings = get_current_holdings_with_quantities(db.session)
        if not holdings:
            empty_totals = {
                "total_value_try": 0,
                "total_cost_try": 0,
                "total_profit_loss_try": 0,
                "total_value_eur": 0
            }
            return render_template('portfolio.html', holdings=[], totals=empty_totals)

        holdings_data = []
        total_portfolio_value_try = 0
        total_portfolio_cost_try = 0

        for symbol, quantity in holdings.items():
            # Get current price
            current_price = get_latest_price(symbol) or 0
            current_value = quantity * current_price

            # Calculate proper cost basis using FIFO
            cost_basis, avg_purchase_price = calculate_cost_basis_fifo(db.session, symbol, quantity)

            # Calculate profit/loss
            profit_loss = current_value - cost_basis

            holdings_data.append({
                "symbol": symbol,
                "quantity": quantity,
                "cost": cost_basis,
                "current_value": round(current_value, 2),
                "profit_loss": round(profit_loss, 2),
                "current_price": round(current_price, 2),
                "average_purchase_price": round(avg_purchase_price, 2),
                "return_percentage": round((profit_loss / cost_basis * 100) if cost_basis > 0 else 0, 2)
            })

            total_portfolio_value_try += current_value
            total_portfolio_cost_try += cost_basis

        # Calculate EUR values
        latest_eur_rate = get_latest_eur_try_rate()
        total_portfolio_value_eur = (total_portfolio_value_try / latest_eur_rate) if latest_eur_rate else 0

        totals = {
            "total_value_try": round(total_portfolio_value_try, 2),
            "total_cost_try": round(total_portfolio_cost_try, 2),
            "total_profit_loss_try": round(total_portfolio_value_try - total_portfolio_cost_try, 2),
            "total_value_eur": round(total_portfolio_value_eur, 2)
        }

        return render_template('portfolio.html', holdings=holdings_data, totals=totals)

    except Exception as e:
        empty_totals = {
            "total_value_try": 0,
            "total_cost_try": 0,
            "total_profit_loss_try": 0,
            "total_value_eur": 0
        }
        return render_template('portfolio.html', error=str(e), holdings=[], totals=empty_totals)
