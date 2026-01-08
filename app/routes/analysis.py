from flask import Blueprint, render_template, request, jsonify
from app import db
from app.utils.portfolio_calculator import get_current_holdings
from app.services.forecast import generate_forecast

bp = Blueprint('analysis', __name__)

@bp.route('/analysis/forecast', methods=['GET', 'POST'])
def forecast():
    holdings = get_current_holdings(db.session)
    selected_symbol = None
    forecast_data = None
    error = None

    if request.method == 'POST':
        selected_symbol = request.form.get('symbol')
        if selected_symbol:
            result = generate_forecast(selected_symbol)
            if "error" in result:
                error = result["error"]
            else:
                forecast_data = result

    return render_template(
        'analysis.html',
        holdings=holdings,
        selected_symbol=selected_symbol,
        forecast_data=forecast_data,
        error=error
    )
