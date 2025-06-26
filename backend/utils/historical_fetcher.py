import yfinance as yf
import pandas as pd
from datetime import date
from typing import List

def get_historical_data(symbols: List[str], start_date: date, end_date: date) -> pd.DataFrame:
    """
    Fetches historical closing prices for a list of symbols over a given date range
    in a single, efficient API call.

    Returns a pandas DataFrame with dates as the index and symbols as columns.
    Missing data for non-trading days is forward-filled.
    """
    if not symbols:
        return pd.DataFrame()
        
    try:
        # Append .IS for BIST stocks if not already present
        formatted_symbols = []
        for s in symbols:
            if s.upper() != 'EURTRY=X' and not s.upper().endswith('.IS'):
                formatted_symbols.append(f"{s}.IS")
            else:
                formatted_symbols.append(s)

        data = yf.download(formatted_symbols, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return pd.DataFrame()

        # We only need the closing prices
        close_prices = data['Close']
        
        # If only one symbol is fetched, it's a Series, convert it to a DataFrame
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.to_frame(name=formatted_symbols[0])

        # Forward-fill missing values for weekends/holidays
        return close_prices.ffill()

    except Exception as e:
        print(f"Error fetching historical bulk data: {e}")
        return pd.DataFrame() 