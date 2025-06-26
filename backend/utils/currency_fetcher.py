import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_historical_eur_try_rate(date: datetime.date) -> float | None:
    """
    Fetches the historical EUR/TRY exchange rate for a specific date using Yahoo Finance.
    This function is now more robust to handle weekends and holidays efficiently.
    """
    try:
        # Fetch the last 30 days of data to ensure we have recent history
        ticker = yf.Ticker("EURTRY=X")
        hist = ticker.history(period="30d")
        
        if hist.empty:
            print(f"Error: No historical data found for EURTRY=X in the last 30 days.")
            return None

        # Convert the timezone-aware index to timezone-naive for comparison
        hist.index = hist.index.tz_localize(None)

        # Use pandas 'asof' to find the most recent price for the given date
        # This is the most efficient way to handle non-trading days (weekends/holidays)
        closest_price = hist.asof(pd.to_datetime(date))
        
        if pd.notna(closest_price['Close']):
            return closest_price['Close']
        else:
            # Fallback if asof fails for some reason
            return hist['Close'].iloc[-1]

    except Exception as e:
        print(f"Error fetching EUR/TRY rate for {date}: {e}")
        return None
    
    return None

def get_latest_eur_try_rate() -> float | None:
    """
    Fetches the latest (most recent) EUR/TRY exchange rate from Yahoo Finance.
    This function now uses the Ticker.history method for more reliable data fetching.
    """
    try:
        ticker = yf.Ticker("EURTRY=X")
        # Get historical market data, fetch for the last 2 days to be safe
        hist = ticker.history(period="2d")
        if not hist.empty:
            # The 'Close' column contains the closing price, .iloc[-1] gets the last one as a float
            return hist['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching latest EUR/TRY rate: {e}")
    
    return None 