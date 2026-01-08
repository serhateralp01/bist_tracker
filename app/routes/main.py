from flask import Blueprint, render_template, current_app
from app import db, models
from app.utils.historical_fetcher import get_enhanced_dashboard_metrics
from app.utils.stock_fetcher import get_bist100_data

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Fetch BIST 100 data
    bist100 = get_bist100_data()

    # Fetch dashboard metrics
    try:
        metrics = get_enhanced_dashboard_metrics(db.session)
    except Exception as e:
        metrics = {"error": str(e)}

    return render_template('dashboard.html', bist100=bist100, metrics=metrics)
