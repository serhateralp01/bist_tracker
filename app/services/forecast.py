import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.utils.historical_fetcher import get_historical_data
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def generate_forecast(symbol: str, periods: int = 30):
    """
    Generates a forecast for the given symbol using Exponential Smoothing (Holt-Winters).
    Returns a dictionary containing historical data and forecast data.
    """
    try:
        # Fetch historical data (last 2 years for better seasonality detection)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=730)

        hist_data = get_historical_data([symbol], start_date, end_date)

        symbol_col = f"{symbol}.IS"
        if hist_data.empty or symbol_col not in hist_data.columns:
            return {"error": f"No data found for {symbol}"}

        series = hist_data[symbol_col].dropna()

        if len(series) < 60:
            return {"error": "Not enough data for forecasting (need at least 60 days)"}

        # Fit Exponential Smoothing Model
        # Seasonal periods: 5 (weekly trading cycle) or 20 (monthly)
        # Using additive trend and no seasonality for robustness on shorter timeframes if needed,
        # but let's try 'add' for trend.
        try:
            model = ExponentialSmoothing(
                series,
                trend='add',
                seasonal=None,
                initialization_method="estimated"
            ).fit()

            forecast = model.forecast(periods)
        except Exception as e:
            # Fallback to simple moving average projection if model fails
            last_val = series.iloc[-1]
            last_trend = series.diff().mean()
            forecast_index = pd.date_range(start=series.index[-1] + timedelta(days=1), periods=periods)
            forecast_values = [last_val + (i+1)*last_trend for i in range(periods)]
            forecast = pd.Series(forecast_values, index=forecast_index)

        # Format for Plotly
        history_dates = series.index.strftime('%Y-%m-%d').tolist()
        history_values = series.values.tolist()

        forecast_dates = forecast.index.strftime('%Y-%m-%d').tolist()
        forecast_values = forecast.values.tolist()

        return {
            "symbol": symbol,
            "history": {
                "dates": history_dates,
                "values": [round(v, 2) for v in history_values]
            },
            "forecast": {
                "dates": forecast_dates,
                "values": [round(v, 2) for v in forecast_values]
            }
        }

    except Exception as e:
        return {"error": str(e)}
