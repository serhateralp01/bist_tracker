import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_historical_rate(date: datetime.date, symbol: str = "EURTRY=X") -> float | None:
    """
    Fetches the historical exchange rate for a specific date using Yahoo Finance.
    """
    try:
        # Fetch the last 30 days of data to ensure we have recent history
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="30d")
        
        if hist.empty:
            print(f"Error: No historical data found for {symbol} in the last 30 days.")
            return None

        # Convert the timezone-aware index to timezone-naive for comparison
        hist.index = hist.index.tz_localize(None)

        # Use pandas 'asof' to find the most recent price for the given date
        closest_price = hist.asof(pd.to_datetime(date))
        
        if pd.notna(closest_price['Close']):
            return closest_price['Close']
        else:
            return hist['Close'].iloc[-1]

    except Exception as e:
        print(f"Error fetching rate {symbol} for {date}: {e}")
        return None

def get_latest_rate(symbol: str = "EURTRY=X") -> float | None:
    """
    Fetches the latest (most recent) exchange rate from Yahoo Finance.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching latest rate for {symbol}: {e}")
    
    return None

def get_historical_eur_try_rate(date: datetime.date) -> float | None:
    return get_historical_rate(date, "EURTRY=X")

def get_latest_eur_try_rate() -> float | None:
    return get_latest_rate("EURTRY=X")

def get_latest_usd_try_rate() -> float | None:
    return get_latest_rate("TRY=X")
