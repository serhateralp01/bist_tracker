from tefas import Crawler
from datetime import datetime, timedelta
import logging
import pandas as pd
from typing import Optional

def get_fund_price(symbol: str) -> float:
    """
    Fetches the latest price for a Turkish Mutual Fund (TEFAS).
    """
    try:
        crawler = Crawler()
        # Fetch for a slightly wider range to ensure we hit a trading day (weekends/holidays)
        # TEFAS usually publishes prices daily.
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # columns: date, code, price
        result = crawler.fetch(start=start_str, end=end_str, columns=["code", "price"], name=symbol)

        if result is None or result.empty:
            logging.warning(f"No TEFAS data found for {symbol}")
            return None

        # Get the first row (assuming it's the latest based on previous checks)
        # tefas-crawler usually returns data sorted by date descending (newest first).
        latest_price = result['price'].iloc[0]

        return float(latest_price)
    except Exception as e:
        logging.error(f"Error fetching fund price for {symbol}: {e}")
        return None

def get_fund_historical_data(symbol: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    """
    Fetches historical data for a fund.
    Returns DataFrame with Index=Date, Columns=[symbol] (Price)
    """
    try:
        crawler = Crawler()
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        result = crawler.fetch(start=start_str, end=end_str, columns=["date", "code", "price"], name=symbol)

        if result is None or result.empty:
            return pd.DataFrame()

        # Process result
        df = result.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()

        # Return just the price column renamed to symbol
        return df[['price']].rename(columns={'price': symbol})

    except Exception as e:
        logging.error(f"Error fetching historical fund data for {symbol}: {e}")
        return pd.DataFrame()
