import yfinance as yf
from datetime import datetime, timedelta

def get_historical_eur_try_rate(date: datetime.date) -> float | None:
    """
    Fetches the historical EUR/TRY exchange rate for a specific date using Yahoo Finance.
    This function now uses the Ticker.history method for more reliable data fetching.
    """
    try:
        ticker = yf.Ticker("EURTRY=X")
        end_date = date + timedelta(days=1)
        # Fetch data for the specific day
        hist = ticker.history(start=date, end=end_date)
        
        if not hist.empty:
            return hist['Close'].iloc[-1]
        
        # If no data for the day (e.g., weekend), backtrack to find the last known rate
        for i in range(1, 7):
            prev_date_start = date - timedelta(days=i)
            prev_date_end = date - timedelta(days=i-1)
            hist = ticker.history(start=prev_date_start, end=prev_date_end)
            if not hist.empty:
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