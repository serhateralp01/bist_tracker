from flask import Flask, render_template, request, jsonify, g, redirect, url_for
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models, crud, schemas
from backend.utils.search_service import search_assets
from backend.utils.portfolio_calculator import calculate_portfolio_value, get_current_holdings_with_quantities, calculate_cost_basis_fifo
from backend.utils.stock_fetcher import get_latest_price
from backend.utils.currency_fetcher import get_latest_eur_try_rate, get_latest_usd_try_rate
from backend.utils.historical_fetcher import get_historical_data, get_portfolio_timeline_data
import pandas as pd
from datetime import datetime, date, timedelta
from collections import defaultdict

# Create Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')

# Create DB Tables
models.Base.metadata.create_all(bind=engine)

# Database Dependency (Flask Middleware)
@app.before_request
def get_db():
    if 'db' not in g:
        g.db = SessionLocal()

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Helpers ---
def calculate_totals(db):
    transactions = db.query(models.Transaction).all()
    holdings_map = {}

    for tx in transactions:
        if tx.type in ['buy', 'sell', 'split']:
            if tx.symbol not in holdings_map:
                holdings_map[tx.symbol] = {'qty': 0, 'asset_type': tx.asset_type or 'STOCK', 'currency': tx.currency or 'TRY'}

            if tx.type == 'buy': holdings_map[tx.symbol]['qty'] += tx.quantity
            elif tx.type == 'sell': holdings_map[tx.symbol]['qty'] -= tx.quantity
            elif tx.type == 'split': holdings_map[tx.symbol]['qty'] += tx.quantity

    total_value_try = 0
    eur_rate = get_latest_eur_try_rate() or 0
    usd_rate = get_latest_usd_try_rate() or 0

    holdings_list = []

    for symbol, data in holdings_map.items():
        quantity = data['qty']
        if quantity <= 0: continue

        asset_type = data['asset_type']
        currency = data['currency']

        current_price = get_latest_price(symbol, asset_type, currency) or 0
        current_value_native = quantity * current_price

        current_value_try = current_value_native
        if currency == "USD": current_value_try = current_value_native * usd_rate
        elif currency == "EUR": current_value_try = current_value_native * eur_rate

        total_value_try += current_value_try

        # P/L Calculation (Simplified)
        cost_basis, _ = calculate_cost_basis_fifo(db, symbol, quantity)
        # Assuming cost_basis is native for now
        profit_loss = current_value_native - cost_basis
        profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0

        holdings_list.append({
            'symbol': symbol,
            'qty': quantity,
            'price': current_price,
            'value_native': current_value_native,
            'value_try': current_value_try,
            'currency': currency,
            'pl': profit_loss,
            'pl_pct': profit_loss_pct
        })

    total_value_usd = (total_value_try / usd_rate) if usd_rate > 0 else 0
    total_value_eur = (total_value_try / eur_rate) if eur_rate > 0 else 0

    return {
        'try': round(total_value_try, 2),
        'usd': round(total_value_usd, 2),
        'eur': round(total_value_eur, 2),
        'holdings': holdings_list
    }

# --- Routes ---

@app.route('/')
def dashboard():
    data = calculate_totals(g.db)
    return render_template('dashboard.html', totals=data, holdings=data['holdings'])

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == 'POST':
        # Handle Add Transaction
        try:
            tx_data = schemas.TransactionCreate(
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                type=request.form['type'],
                symbol=request.form['symbol'],
                quantity=float(request.form['quantity']),
                price=float(request.form['price']),
                currency=request.form.get('currency', 'TRY'),
                asset_type=request.form.get('asset_type', 'STOCK')
            )
            crud.create_transaction(g.db, tx_data)
            return redirect(url_for('transactions'))
        except Exception as e:
            return str(e), 400

    transactions = crud.get_transactions(g.db, limit=100)
    return render_template('transactions.html', transactions=transactions)

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

# --- API Endpoints ---

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')
    if not q: return jsonify([])
    results = search_assets(q)
    return jsonify(results)

@app.route('/api/chart')
def api_chart():
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=365) # Default 1 year history

    data = get_portfolio_timeline_data(g.db, start_date, end_date)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
