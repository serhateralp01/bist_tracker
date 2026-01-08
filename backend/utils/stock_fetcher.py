import yfinance as yf
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
import time
from .fund_fetcher import get_fund_price

# Configure structured logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_api_call(func_name, symbol, status, detail=""):
    logging.info(f"API_CALL - Function: {func_name}, Symbol: {symbol}, Status: {status}, Detail: {detail}")

def get_latest_price(symbol: str, asset_type: str = "STOCK", currency: str = "TRY") -> Optional[float]:
    """
    Fetches the latest price for a given symbol.
    Supports STOCKS and FUNDS.
    Handles different currencies for stocks.
    """
    start_time = time.time()

    # 1. Handle Funds (TEFAS)
    if asset_type == "FUND":
        price = get_fund_price(symbol)
        duration = time.time() - start_time
        if price is not None:
             log_api_call('get_latest_price', symbol, 'SUCCESS', f'Type: FUND, Duration: {duration:.2f}s')
             return price
        else:
             log_api_call('get_latest_price', symbol, 'FAIL', f'Type: FUND, Duration: {duration:.2f}s')
             return None

    # 2. Handle Stocks (YFinance)
    try:
        # Determine ticker suffix based on currency/market
        # If it's TRY and not explicitly foreign, append .IS
        # If it's USD or EUR, assume it's a foreign ticker (e.g. AAPL, BMW.DE)

        ticker_symbol = symbol
        if currency == "TRY" and not symbol.endswith(".IS"):
             # Assumption: If currency is TRY, it's likely BIST.
             # Unless the user explicitly put .IS already.
             ticker_symbol = symbol + ".IS"

        # If currency is NOT TRY (e.g. USD), use symbol as is (e.g. AAPL)

        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1d")
        duration = time.time() - start_time

        if hist.empty:
            log_api_call('get_latest_price', symbol, 'FAIL', f'Ticker: {ticker_symbol}, Duration: {duration:.2f}s, Reason: History is empty')
            return None

        log_api_call('get_latest_price', symbol, 'SUCCESS', f'Ticker: {ticker_symbol}, Duration: {duration:.2f}s')
        return round(hist['Close'].iloc[-1], 2)

    except Exception as e:
        duration = time.time() - start_time
        log_api_call('get_latest_price', symbol, 'EXCEPTION', f'Duration: {duration:.2f}s, Error: {e}')
        return None

def get_bist100_data() -> Optional[Dict]:
    """
    Fetch BIST 100 index data from Yahoo Finance
    Returns current value, change, change percentage, and volume
    """
    try:
        # BIST 100 ticker symbol on Yahoo Finance
        ticker = yf.Ticker("XU100.IS")
        
        # Get 2 days of data to calculate change
        hist = ticker.history(period="2d")
        if hist.empty or len(hist) < 1:
            return None
            
        # Get current and previous close
        current_close = hist['Close'].iloc[-1]
        
        # If we have more than one day, calculate change from previous day
        if len(hist) > 1:
            previous_close = hist['Close'].iloc[-2]
            change = current_close - previous_close
            change_percent = (change / previous_close) * 100
        else:
            # If only one day available, try to get intraday data
            intraday_hist = ticker.history(period="1d", interval="1m")
            if not intraday_hist.empty and len(intraday_hist) > 1:
                # Use opening price as reference for intraday change
                opening_price = intraday_hist['Open'].iloc[0]
                change = current_close - opening_price
                change_percent = (change / opening_price) * 100
            else:
                change = 0
                change_percent = 0
        
        # Get volume (if available)
        volume = hist['Volume'].iloc[-1] if not hist['Volume'].empty else 0
        
        # Format volume in readable format
        if volume >= 1_000_000_000:
            volume_str = f"{volume / 1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            volume_str = f"{volume / 1_000_000:.1f}M"
        elif volume >= 1_000:
            volume_str = f"{volume / 1_000:.1f}K"
        else:
            volume_str = str(int(volume))
            
        return {
            "value": round(current_close, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": volume_str,
            "last_update": datetime.now().strftime("%H:%M")
        }
        
    except Exception as e:
        print(f"Error fetching BIST 100 data: {e}")
        return None

def get_currency_rate(from_currency: str = "EUR", to_currency: str = "TRY") -> Optional[float]:
    """
    Fetch currency exchange rate
    """
    try:
        symbol = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        return round(hist['Close'].iloc[-1], 4)
    except Exception:
        return None
